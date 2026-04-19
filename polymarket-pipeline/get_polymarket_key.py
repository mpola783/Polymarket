from py_clob_client.client import ClobClient

client = ClobClient(
    "https://clob.polymarket.com",
    key="",
    chain_id=137
)

creds = client.create_or_derive_api_creds()
print("API Key:", creds.api_key)
print("Secret:", creds.api_secret)
print("Passphrase:", creds.api_passphrase)
