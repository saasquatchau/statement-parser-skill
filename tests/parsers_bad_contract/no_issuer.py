"""A candidate Parser missing ISSUER, used to test the contract check."""
STATEMENT_FORMAT = "No Issuer"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["PROBE BANK"]


def parse(text):
    raise NotImplementedError
