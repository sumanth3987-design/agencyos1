'''PostgreSQL-specific payment tests.

These tests are opt-in. They run only when TEST_DATABASE_URL points to a
dedicated PostgreSQL test database and psycopg is installed.
'''

import os
import threading

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

from app.extensions import db as _db
from app.models import User, Project, Payment
from werkzeug.security import generate_password_hash


try:
    import psycopg  # noqa: F401

    _PSYCOPG_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    _PSYCOPG_AVAILABLE = False


pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not os.getenv('TEST_DATABASE_URL'),
        reason='TEST_DATABASE_URL is not set',
    ),
    pytest.mark.skipif(
        not _PSYCOPG_AVAILABLE,
        reason='psycopg is not installed',
    ),
]


def _make_razorpay_order(order_id='order_pg_test', amount=499900,
                         currency='INR', status='created'):
    return {
        'id': order_id,
        'amount': amount,
        'currency': currency,
        'status': status,
        'receipt': 'agencyos_project_1',
    }


def test_payment_unique_constraints_and_indexes_exist(app, db):
    '''PostgreSQL exposes all three uniqueness definitions.'''
    with app.app_context():
        inspector = inspect(db.engine)
        index_names = {index['name'] for index in inspector.get_indexes('payment')}
        constraint_names = {
            constraint['name']
            for constraint in inspector.get_unique_constraints('payment')
        }
        assert 'uq_payment_razorpay_order_id' in (index_names | constraint_names)
        assert 'uq_payment_razorpay_payment_id_partial' in index_names
        assert 'uq_payment_project_customer_created' in index_names

        rows = db.session.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes "
                "WHERE tablename = 'payment'"
            )
        ).mappings().all()
        definitions = {row['indexname']: row['indexdef'] for row in rows}

        payment_index = definitions['uq_payment_razorpay_payment_id_partial']
        assert 'razorpay_payment_id' in payment_index
        assert 'IS NOT NULL' in payment_index.upper()

        created_index = definitions['uq_payment_project_customer_created']
        assert 'project_id' in created_index
        assert 'customer_id' in created_index
        assert 'Created' in created_index
def test_concurrent_duplicate_created_payment_postgres(app, db):
    '''Two PostgreSQL sessions inserting the same open-payment key: one wins.'''
    with app.app_context():
        user = User(
            name='PG Concurrency Customer',
            email='pg_concurrency@example.com',
            password=generate_password_hash('Password123'),
            role='customer',
        )
        db.session.add(user)
        db.session.commit()
        project = Project(
            customer_id=user.id,
            service='Website',
            package='Basic Website',
            requirements='PG concurrency test',
            status='Payment Pending',
        )
        db.session.add(project)
        db.session.commit()
        user_id = user.id
        project_id = project.id

    results = []
    barrier = threading.Barrier(2, timeout=10)

    def worker(order_id):
        try:
            barrier.wait(timeout=10)
        except threading.BrokenBarrierError:
            results.append('barrier_error')
            return
        try:
            with app.app_context():
                payment = Payment(
                    project_id=project_id,
                    customer_id=user_id,
                    razorpay_order_id=order_id,
                    amount=4999,
                    currency='INR',
                    status='Created',
                )
                db.session.add(payment)
                db.session.commit()
                db.session.remove()
                results.append('ok')
        except IntegrityError:
            try:
                db.session.rollback()
                db.session.remove()
            except Exception:
                pass
            results.append('IntegrityError')
        except Exception as exc:  # pragma: no cover - diagnostic only
            try:
                db.session.rollback()
                db.session.remove()
            except Exception:
                pass
            results.append(type(exc).__name__)

    threads = [
        threading.Thread(target=worker, args=('order_pg_first',), daemon=True),
        threading.Thread(target=worker, args=('order_pg_second',), daemon=True),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in threads)
    assert sorted(results) == ['IntegrityError', 'ok']

    with app.app_context():
        count = Payment.query.filter_by(
            project_id=project_id,
            customer_id=user_id,
            status='Created',
        ).count()
        assert count == 1
        db.session.remove()


def test_concurrent_payment_verification_postgres(app, db):
    '''Two PostgreSQL sessions claiming one Created payment: one update wins.'''
    with app.app_context():
        user = User(
            name='PG Claim Customer',
            email='pg_claim@example.com',
            password=generate_password_hash('Password123'),
            role='customer',
        )
        db.session.add(user)
        db.session.commit()
        project = Project(
            customer_id=user.id,
            service='Website',
            package='Basic Website',
            requirements='PG claim test',
            status='Payment Pending',
        )
        db.session.add(project)
        db.session.commit()
        payment = Payment(
            project_id=project.id,
            customer_id=user.id,
            razorpay_order_id='order_pg_claim',
            amount=4999,
            currency='INR',
            status='Created',
        )
        db.session.add(payment)
        db.session.commit()
        payment_id = payment.id

    results = []
    barrier = threading.Barrier(2, timeout=10)

    def worker(payment_value):
        try:
            barrier.wait(timeout=10)
        except threading.BrokenBarrierError:
            results.append('barrier_error')
            return
        try:
            with app.app_context():
                updated = Payment.query.filter_by(
                    id=payment_id, status='Created'
                ).update(
                    {
                        'status': 'Paid',
                        'razorpay_payment_id': payment_value,
                    },
                    synchronize_session=False,
                )
                db.session.commit()
                db.session.remove()
                results.append(updated)
        except Exception as exc:  # pragma: no cover - diagnostic only
            try:
                db.session.rollback()
                db.session.remove()
            except Exception:
                pass
            results.append('error:' + type(exc).__name__)

    threads = [
        threading.Thread(target=worker, args=('pay_pg_first',), daemon=True),
        threading.Thread(target=worker, args=('pay_pg_second',), daemon=True),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in threads)
    assert not any(
        isinstance(result, str) and result.startswith('error:')
        for result in results
    )
    assert sorted(results) == [0, 1]

    with app.app_context():
        final_payment = db.session.get(Payment, payment_id)
        assert final_payment is not None
        assert final_payment.status == 'Paid'
        assert final_payment.razorpay_payment_id in {'pay_pg_first', 'pay_pg_second'}
        db.session.remove()

def test_integrity_error_rollback_recovers_session_postgres(app, db):
    '''A rolled-back IntegrityError leaves the PostgreSQL session usable.'''
    with app.app_context():
        user = User(
            name='PG Rollback Customer',
            email='pg_rollback@example.com',
            password=generate_password_hash('Password123'),
            role='customer',
        )
        db.session.add(user)
        db.session.commit()
        project = Project(
            customer_id=user.id,
            service='Website',
            package='Basic Website',
            requirements='PG rollback test',
            status='Payment Pending',
        )
        db.session.add(project)
        db.session.commit()

        first_payment = Payment(
            project_id=project.id,
            customer_id=user.id,
            razorpay_order_id='order_pg_rollback',
            amount=4999,
            currency='INR',
            status='Created',
        )
        db.session.add(first_payment)
        db.session.commit()

        duplicate_payment = Payment(
            project_id=project.id,
            customer_id=user.id,
            razorpay_order_id='order_pg_rollback',
            amount=4999,
            currency='INR',
            status='Created',
        )
        db.session.add(duplicate_payment)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        second_project = Project(
            customer_id=user.id,
            service='Website',
            package='Basic Website',
            requirements='PG rollback recovery',
            status='Payment Pending',
        )
        db.session.add(second_project)
        db.session.commit()
        recovered_payment = Payment(
            project_id=second_project.id,
            customer_id=user.id,
            razorpay_order_id='order_pg_rollback_recovered',
            amount=4999,
            currency='INR',
            status='Created',
        )
        db.session.add(recovered_payment)
        db.session.commit()

        assert recovered_payment.id is not None
        db.session.remove()


def test_duplicate_order_creation_conflict_recovers_postgres(app, client, login, factories, csrf_token, monkeypatch):
    '''Simulated order-creation conflict is handled without a 500 under PostgreSQL.'''
    customer_id = factories.user('customer', 'pg_racesim@example.com')
    project_id = factories.project(customer_id, status='Payment Pending')
    login('pg_racesim@example.com', 'customer')

    fake_order = _make_razorpay_order(order_id='order_pg_racesim')

    from app.extensions import db as _db

    original_commit = _db.session.commit
    state = {'raised': False}

    def flaky_commit():
        if not state['raised']:
            state['raised'] = True
            raise IntegrityError('race', None, None)
        return original_commit()

    monkeypatch.setattr(_db.session, 'commit', flaky_commit)

    with patch(
        'app.blueprints.payments.razorpay_client.order.create',
        return_value=fake_order,
    ):
        response = client.post(
            '/payment/create-order/' + str(project_id),
            data={'csrf_token': csrf_token},
            follow_redirects=False,
        )

    assert response.status_code in (200, 400)


def test_payment_and_project_state_preserved_after_failed_verification_postgres(
    app, client, login, factories, csrf_token
):
    '''Failed verification leaves payment and project states unchanged.'''
    customer_id = factories.user('customer', 'pg_state@example.com')
    project_id = factories.project(customer_id, status='Payment Pending')
    factories.payment(
        project_id, customer_id, razorpay_order_id='order_pg_state', status='Created'
    )
    login('pg_state@example.com', 'customer')

    import razorpay

    with patch(
        'app.blueprints.payments.razorpay_client.utility.verify_payment_signature',
        side_effect=razorpay.errors.SignatureVerificationError('bad signature'),
    ):
        response = client.post(
            '/payment/verify',
            data=__import__('json').dumps({
                'razorpay_order_id': 'order_pg_state',
                'razorpay_payment_id': 'pay_pg_state',
                'razorpay_signature': 'bad_sig',
            }),
            content_type='application/json',
            headers={'X-CSRFToken': csrf_token},
            follow_redirects=False,
        )

    assert response.status_code == 400

    with app.app_context():
        payment = Payment.query.filter_by(
            razorpay_order_id='order_pg_state'
        ).first()
        assert payment is not None
        assert payment.status == 'Created'
        assert payment.razorpay_payment_id is None
        project = _db.session.get(Project, project_id)
        assert project is not None
        assert project.status == 'Payment Pending'
        _db.session.remove()
