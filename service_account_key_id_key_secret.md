
curl --location 'https://console.cloud.ru/u-api/bff-console/v1/service-accounts/acb0df63-9711-4167-adc2-9eac4fd0d5df/access_keys' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer ...' \
--data '{"description":"<description>","ttl": 30}'

ttl in days



answer:

{
    "id": "6b9b4e75-8640-4b74-a65b-46bf66cd3ed8",
    "service_account_id": "acb0df63-9711-4167-adc2-9eac4fd0d5df",
    "description": "3212",
    "key_id": "443dfe8f0692bc163dcaf07c0b0346f6",
    "secret": "30c519addbb9b8e91af26934a56657b0",
    "created_at": "2026-04-01T10:17:08.386182229Z",
    "expired_at": "2026-04-02T10:17:08.386182229Z"
}