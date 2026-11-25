import argparse
from getpass import getpass

from backend.auth.service import AccountConflict, bootstrap_admin


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision the first Smart Stadium administrator."
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="User ID to assign to the initial administrator.",
    )
    args = parser.parse_args()

    password = getpass("Administrator password (12+ characters): ")
    confirmation = getpass("Confirm administrator password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")

    try:
        bootstrap_admin(args.user_id, password)
    except (ValueError, AccountConflict) as error:
        parser.error(str(error))

    print("Initial administrator provisioned.")


if __name__ == "__main__":
    main()
