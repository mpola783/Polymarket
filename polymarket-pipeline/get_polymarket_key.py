from py_clob_client.client import ClobClient

client = ClobClient(
    "https://clob.polymarket.com",
    key="f68bafab53b3a4595a136c58fe50b2caf65de97a2edf9bce1453a25681985d90",
    chain_id=137
)

creds = client.create_or_derive_api_creds()
print("API Key:", creds.api_key)
print("Secret:", creds.api_secret)
print("Passphrase:", creds.api_passphrase)
