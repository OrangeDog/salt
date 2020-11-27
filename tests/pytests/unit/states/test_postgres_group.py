import pytest
import salt.modules.postgres as postgres
import salt.states.postgres_group as postgres_group
from tests.support.mock import create_autospec, patch

DB_ARGS = {
    "runas": None,
    "host": None,
    "port": None,
    "maintenance_db": None,
    "user": None,
    "password": None,
}


@pytest.fixture(name="md5_pw")
def fixture_md5_pw():
    # 'md5' + md5('password' + 'groupname')
    return "md58b14c378fab8ef0dc227f4e6d6787a87"


@pytest.fixture(name="existing_group")
def fixture_existing_group():
    return {
        "superuser": False,
        "inherits privileges": True,
        "can create roles": False,
        "can create databases": False,
        "can update system catalogs": None,
        "can login": False,
        "replication": False,
        "connections": None,
        "expiry time": None,
        "defaults variables": "",
        "password": "",
        "groups": [],
    }


@pytest.fixture(name="test_mode")
def fixture_test_mode():
    with patch.dict(postgres_group.__opts__, {"test": True}):
        yield


@pytest.fixture(name="mocks")
def fixture_mocks():
    return {
        "postgres.role_get": create_autospec(postgres.role_get, return_value=None),
        "postgres.user_exists": create_autospec(
            postgres.user_exists, return_value=False
        ),
        "postgres.group_create": create_autospec(
            postgres.group_create, return_value=True
        ),
        "postgres.group_update": create_autospec(
            postgres.group_update, return_value=True
        ),
        "postgres.group_remove": create_autospec(
            postgres.group_remove, return_value=True
        ),
    }


@pytest.fixture(autouse=True)
def setup_loader(mocks):
    setup_loader_modules = {
        postgres_group: {"__opts__": {"test": False}, "__salt__": mocks},
        postgres: {"__opts__": {"test": False}},
    }
    with pytest.helpers.loader_mock(setup_loader_modules) as loader_mock:
        yield loader_mock


# ==========
# postgres_group.present
# ==========


def test_present_create_basic(mocks):
    assert postgres_group.present("groupname") == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": "Present"},
        "comment": "The group groupname has been created",
    }
    mocks["postgres.role_get"].assert_called_once_with(
        "groupname", return_password=True, **DB_ARGS
    )
    mocks["postgres.group_create"].assert_called_once_with(
        groupname="groupname",
        createdb=None,
        createroles=None,
        encrypted="md5",
        superuser=None,
        login=None,
        inherit=None,
        replication=None,
        rolepassword=None,
        groups=None,
        **DB_ARGS
    )
    mocks["postgres.group_update"].assert_not_called()


@pytest.mark.usefixtures("test_mode")
def test_present_create_basic_test(mocks):
    assert postgres_group.present("groupname") == {
        "name": "groupname",
        "result": None,
        "changes": {},
        "comment": "Group groupname is set to be created",
    }
    mocks["postgres.role_get"].assert_called_once_with(
        "groupname", return_password=True, **DB_ARGS
    )
    mocks["postgres.group_create"].assert_not_called()
    mocks["postgres.group_update"].assert_not_called()


def test_present_exists_basic(mocks, existing_group):
    mocks["postgres.role_get"].return_value = existing_group

    assert postgres_group.present("groupname") == {
        "name": "groupname",
        "result": True,
        "changes": {},
        "comment": "Group groupname is already present",
    }
    mocks["postgres.role_get"].assert_called_once_with(
        "groupname", return_password=True, **DB_ARGS
    )
    mocks["postgres.group_create"].assert_not_called()
    mocks["postgres.group_update"].assert_not_called()


def test_present_create_basic_error(mocks):
    mocks["postgres.group_create"].return_value = False

    assert postgres_group.present("groupname") == {
        "name": "groupname",
        "result": False,
        "changes": {},
        "comment": "Failed to create group groupname",
    }
    mocks["postgres.role_get"].assert_called_once_with(
        "groupname", return_password=True, **DB_ARGS
    )
    mocks["postgres.group_create"].assert_called_once()
    mocks["postgres.group_update"].assert_not_called()


def test_present_create_md5_password(mocks, md5_pw):
    assert postgres_group.present("groupname", password="password", encrypted=True) == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": "Present"},
        "comment": "The group groupname has been created",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_called_once_with(
        groupname="groupname",
        createdb=None,
        createroles=None,
        encrypted=True,
        superuser=None,
        login=None,
        inherit=None,
        replication=None,
        rolepassword=md5_pw,
        groups=None,
        **DB_ARGS
    )
    mocks["postgres.group_update"].assert_not_called()


def test_present_create_plain_password(mocks):
    assert postgres_group.present(
        "groupname", password="password", encrypted=False
    ) == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": "Present"},
        "comment": "The group groupname has been created",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_called_once_with(
        groupname="groupname",
        createdb=None,
        createroles=None,
        encrypted=False,
        superuser=None,
        login=None,
        inherit=None,
        replication=None,
        rolepassword="password",
        groups=None,
        **DB_ARGS
    )
    mocks["postgres.group_update"].assert_not_called()


def test_present_create_md5_password_default_plain(mocks, monkeypatch, md5_pw):
    monkeypatch.setattr(postgres, "_DEFAULT_PASSWORDS_ENCRYPTION", False)
    test_present_create_md5_password(mocks, md5_pw)


def test_present_create_md5_password_default_encrypted(mocks, monkeypatch, md5_pw):
    monkeypatch.setattr(postgres, "_DEFAULT_PASSWORDS_ENCRYPTION", True)

    assert postgres_group.present("groupname", password="password") == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": "Present"},
        "comment": "The group groupname has been created",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_called_once_with(
        groupname="groupname",
        createdb=None,
        createroles=None,
        encrypted=True,
        superuser=None,
        login=None,
        inherit=None,
        replication=None,
        rolepassword=md5_pw,
        groups=None,
        **DB_ARGS
    )
    mocks["postgres.group_update"].assert_not_called()


def test_present_create_md5_prehashed(mocks, md5_pw):
    assert postgres_group.present("groupname", password=md5_pw, encrypted=True) == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": "Present"},
        "comment": "The group groupname has been created",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_called_once_with(
        groupname="groupname",
        createdb=None,
        createroles=None,
        encrypted=True,
        superuser=None,
        login=None,
        inherit=None,
        replication=None,
        rolepassword=md5_pw,
        groups=None,
        **DB_ARGS
    )
    mocks["postgres.group_update"].assert_not_called()


def test_present_md5_matches(mocks, existing_group, md5_pw):
    existing_group["password"] = md5_pw
    mocks["postgres.role_get"].return_value = existing_group

    assert postgres_group.present("groupname", password="password", encrypted=True) == {
        "name": "groupname",
        "result": True,
        "changes": {},
        "comment": "Group groupname is already present",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_not_called()
    mocks["postgres.group_update"].assert_not_called()


def test_present_md5_matches_prehashed(mocks, existing_group, md5_pw):
    existing_group["password"] = md5_pw
    mocks["postgres.role_get"].return_value = existing_group

    assert postgres_group.present("groupname", password=md5_pw, encrypted=True) == {
        "name": "groupname",
        "result": True,
        "changes": {},
        "comment": "Group groupname is already present",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_not_called()
    mocks["postgres.group_update"].assert_not_called()


def test_present_update_md5_password(mocks, existing_group, md5_pw):
    existing_group["password"] = "md500000000000000000000000000000000"
    mocks["postgres.role_get"].return_value = existing_group

    assert postgres_group.present("groupname", password="password", encrypted=True) == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": {"password": True}},
        "comment": "The group groupname has been updated",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_not_called()
    mocks["postgres.group_update"].assert_called_once_with(
        groupname="groupname",
        createdb=None,
        createroles=None,
        encrypted=True,
        superuser=None,
        login=None,
        inherit=None,
        replication=None,
        rolepassword=md5_pw,
        groups=None,
        **DB_ARGS
    )


def test_present_update_error(mocks, existing_group):
    existing_group["password"] = "md500000000000000000000000000000000"
    mocks["postgres.role_get"].return_value = existing_group
    mocks["postgres.group_update"].return_value = False

    assert postgres_group.present("groupname", password="password", encrypted=True) == {
        "name": "groupname",
        "result": False,
        "changes": {},
        "comment": "Failed to update group groupname",
    }
    mocks["postgres.role_get"].assert_called_once()
    mocks["postgres.group_create"].assert_not_called()
    mocks["postgres.group_update"].assert_called_once()


def test_present_update_password_no_check(mocks, existing_group, md5_pw):
    mocks["postgres.role_get"].return_value = existing_group

    assert postgres_group.present(
        "groupname", password="password", encrypted=True, refresh_password=True
    ) == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": {"password": True}},
        "comment": "The group groupname has been updated",
    }
    mocks["postgres.role_get"].assert_called_once_with(
        "groupname", return_password=False, **DB_ARGS
    )
    mocks["postgres.group_create"].assert_not_called()
    mocks["postgres.group_update"].assert_called_once_with(
        groupname="groupname",
        createdb=None,
        createroles=None,
        encrypted=True,
        superuser=None,
        login=None,
        inherit=None,
        replication=None,
        rolepassword=md5_pw,
        groups=None,
        **DB_ARGS
    )


# ==========
# postgres_group.absent
# ==========


def test_absent_delete(mocks):
    mocks["postgres.user_exists"].return_value = True

    assert postgres_group.absent("groupname") == {
        "name": "groupname",
        "result": True,
        "changes": {"groupname": "Absent"},
        "comment": "Group groupname has been removed",
    }
    mocks["postgres.user_exists"].assert_called_once_with("groupname", **DB_ARGS)
    mocks["postgres.group_remove"].assert_called_once_with("groupname", **DB_ARGS)


@pytest.mark.usefixtures("test_mode")
def test_absent_test(mocks):
    mocks["postgres.user_exists"].return_value = True

    assert postgres_group.absent("groupname") == {
        "name": "groupname",
        "result": None,
        "changes": {},
        "comment": "Group groupname is set to be removed",
    }
    mocks["postgres.user_exists"].assert_called_once_with("groupname", **DB_ARGS)
    mocks["postgres.group_remove"].assert_not_called()


def test_absent_already(mocks):
    mocks["postgres.user_exists"].return_value = False

    assert postgres_group.absent("groupname") == {
        "name": "groupname",
        "result": True,
        "changes": {},
        "comment": "Group groupname is not present, so it cannot be removed",
    }
    mocks["postgres.user_exists"].assert_called_once_with("groupname", **DB_ARGS)
    mocks["postgres.group_remove"].assert_not_called()


def test_absent_error(mocks):
    mocks["postgres.user_exists"].return_value = True
    mocks["postgres.group_remove"].return_value = False

    assert postgres_group.absent("groupname") == {
        "name": "groupname",
        "result": False,
        "changes": {},
        "comment": "Group groupname failed to be removed",
    }
    mocks["postgres.user_exists"].assert_called_once()
    mocks["postgres.group_remove"].assert_called_once()
