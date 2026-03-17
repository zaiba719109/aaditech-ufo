"""Tests for RBAC model scaffolding (Week 6 foundation)."""

from server.extensions import db
from server.models import Organization, User, Role, Permission


def test_create_user_role_permission_relationships(app_fixture):
    with app_fixture.app_context():
        org = Organization(name='RBAC Org', slug='rbac-org', is_active=True)
        db.session.add(org)
        db.session.commit()

        user = User(
            organization_id=org.id,
            email='admin@rbac.org',
            full_name='Admin User',
            password_hash='hashed-password',
            is_active=True,
        )
        role = Role(
            organization_id=org.id,
            name='admin',
            description='Administrator role',
            is_system=True,
        )
        permission = Permission(
            code='tenant.manage.rbac-test',
            description='Manage tenant settings',
        )

        role.permissions.append(permission)
        user.roles.append(role)

        db.session.add(permission)
        db.session.add(role)
        db.session.add(user)
        db.session.commit()

        stored_user = User.query.filter_by(email='admin@rbac.org').first()
        assert stored_user is not None
        assert len(stored_user.roles) == 1
        assert stored_user.roles[0].name == 'admin'
        assert stored_user.roles[0].permissions[0].code == 'tenant.manage.rbac-test'


def test_user_email_unique_per_organization(app_fixture):
    with app_fixture.app_context():
        org1 = Organization(name='RBAC One', slug='rbac-one', is_active=True)
        org2 = Organization(name='RBAC Two', slug='rbac-two', is_active=True)
        db.session.add(org1)
        db.session.add(org2)
        db.session.commit()

        user1 = User(
            organization_id=org1.id,
            email='same@company.com',
            full_name='User One',
            password_hash='hash-1',
        )
        user2 = User(
            organization_id=org2.id,
            email='same@company.com',
            full_name='User Two',
            password_hash='hash-2',
        )

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        assert User.query.filter_by(email='same@company.com').count() == 2
