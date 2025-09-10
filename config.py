#!/usr/bin/env python3
"""
Centralized configuration for All In 2025 scraping scripts
Contains authentication tokens, headers, and API endpoints
"""

# API Endpoints
GRAPHQL_URL = "https://app.swapcard.com/api/graphql"
BASE_URL = "https://app.swapcard.com"

# Event Configuration
EVENT_ID = "RXZlbnRfMjU3MTcxMQ=="  # All In 2025 event ID
EVENT_SLUG = "all-in-2025"
VIEW_ID = "RXZlbnRWaWV3XzEwNTU5ODE="

# Authentication Headers
HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb3JlQXBpVXNlcklkIjoiVlhObGNsOHlOVEUxT0RVNU1RPT0iLCJwZXJtaXNzaW9ucyI6W10sInNlc3Npb25JZCI6IjY4YzFjMGFkZDYwYjNjODFkOTE2NWM5YiIsInR5cGUiOiJhY2Nlc3MtdG9rZW4iLCJ1c2VySWQiOiI2ODc5MjAxNWVhZDUyZmY1ZjA3MzcxNmIiLCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJpYXQiOjE3NTc1MzI5MjYsImV4cCI6MTc1NzYxOTMyNiwiaXNzIjoiYXV0aC1hcGkifQ.ZCdBYB1_bomfLh-mSfZltSXUXuMF4DZFOHARRGQRcXz51mzqYJ442xDPoDpGsnAEbxW-jvkCLvJW1ocasfBNkEjNJJFxaluyIBVO6hnX8_zRyRs1yP1gfSFvvWa7ezmF8umfYIuUFUnKQKsG4c5qTwNjvGM6TbnQH8H-FAlYw4jh-2xvR31fwRTWdguyd-5uYEtP6wL2OXqwoFBZT0ou5Taq2SY4jTGEqsOUkDqfw8cF_C9ZBslf8MOcaoEKUcu17FPGTpRwyqhFLmP3atOxm5aw6iUGEG0jw7O6iOFTcTTq0TrkkjpDafNcUNaaEFB3lhBVPi0K7z-f4-ONrYo7PoiI7HK7OuETNE_HpuirXeOl1vJaNLziatbIOyGyvrZmjrDxwJBM8AYrXV6JDdGr4_JjlI75DVWRwaV3V2F6GS4DgFAc66SfUVfoFF1bcZ6u0JO2lRbS4UVPNu8UIuBaCKeiQfuUWxlVlfEUi-WUUviVvwP8t8NZ4d1AVQUdIAPT_VBxgXFeakJ3RJlKcmQph0FyLkk9Ul_tXIfdlinTLeMLMx9GfIBEXVk0R4AKSeb7dp00xJQ_2MI7ChORKJLOMZ2o7obb9X40A_aH3vwp4d-DqnfETaEEPar3inwhZBPBJqbFa__F7TuYDp_1ZJJfwvCemUglLbXmeGJ8dCiDjg0',
    'content-type': 'application/json',
    'dnt': '1',
    'origin': 'https://app.swapcard.com',
    'referer': 'https://app.swapcard.com/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'x-client-origin': 'app.swapcard.com',
    'x-client-platform': 'Event App',
    'x-client-version': '2.309.297',
    'x-feature-flags': 'fixBackwardPaginationOrder'
}

# Cookies
COOKIES = {
    'next-i18next': 'en-US',
    'swapcard-last-visited-event': 'all-in-2025',
    'swapcard-cookie-consent': '{"accepted":true}',
    'swapcard-auth-api-refresh-token': 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uSWQiOiI2OGMxYzBhZGQ2MGIzYzgxZDkxNjVjOWIiLCJ0eXBlIjoicmVmcmVzaC10b2tlbiIsInVzZXJJZCI6IjY4NzkyMDE1ZWFkNTJmZjVmMDczNzE2YiIsImlhdCI6MTc1NzUyODIzNywiaXNzIjoiYXV0aC1hcGkifQ.Ud2to5WyR9qd2f8M0DQrpnAqV2iN6GLAgN8RC4SDFeG0Q8xmLKgNONTak6DWDr3eUAYq8B-jreO8MPvLzmXhjbLNv3iTAEDWmlAQMR_Y9dcfqSMGa0PvCX8guo2sv9lBPl5z7CcVWrld79jLM0hkMCpal0-NGOSGg_BTDNcLCFD3QfHjQtjpkwI0xezcwmlSHmTdLVepkrQfY5ge9WyoGunYVhhitlUxVyX0funL_z-ot-95it8NKgJ8kSG3RxMxmqoW2Yk0VQo812fpjG18Sd5Ryo94gjs4w43-z_YAnWPz5B0-Lf1aWcCUHes7AZtahi27oZBtDnlBb1AEp7rJqqPlDkqqpSdReZTIFr8QjNolKAx4DUR2rghvZI1sN2BtRNBHG9mgmRsPV7WiNtpdZjuFM57G2QRJmG-fHmBUNXIajqmhcd7DQXltTZCfQWl0P9ixvW0Xmt5Xl0vCUI9N441wreIV95HZwk1AyP3UXViF7CF6drCMeC_LQTQYu5PT6V_cmrLwXOpniUK5TARcibktF1qj_4wqKmGBy2qV1AWB11EzQ9V-UDAp_n6VxxfwquOcZxTHgkd0g33Zqp9lOthTgRhXpnBF3aPQeGDA6weLH8t3jaTIftNW6TqLXivWfzstXnsILTFQqNwjK8sDZeWG1V0M3F6gKu8WYZTDtIo',
    'swapcard-last-visited-community': 'all-in'
}

# Old cookie-based auth (for scrape_all_attendees_complete.py which uses different endpoint)
OLD_COOKIES = {
    '_swp_session_': 'eyJpdiI6IjJLV001V2tiZEl5RTJ5dHFIWUpjMUE9PSIsInZhbHVlIjoiM2wxVjl3OFBzRUthN3BJanJRRVJ5K2tNOThRN2R6VDltTGJnNm9aNXR5THQxS2JlMEpqblhoSGdCTmh2SWw5VFJTUm45RTUweE1xdlB3Q0xUNWNXczBJQnEzZFo5OVJ1MTE3VUkrT1BybTl3ZHdKM0dId2crTVluMVFsU09HbzkiLCJtYWMiOiI1ZWU3NTMwNGU1YTQ0ZjgyYzNlOGEzY2M5ZDk4Y2NlNDI4OGMxZGNhYTRlMzU0MWRmOTBhOTk0N2I0NDZmOWNkIn0%3D',
    '_swp_token_': '%7B%22accessToken%22%3A%22eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjJIaDl2SlFoS1RTbGYxdFVBS2oybyJ9.eyJpc3MiOiJodHRwczovL3N3YXBjYXJkLmV1LmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw2NzZjN2Y0MDlkMDIzMzg5ZjJhNGE3YzciLCJhdWQiOlsiaHR0cHM6Ly9hcGkuc3dhcGNhcmQuY29tLyIsImh0dHBzOi8vc3dhcGNhcmQuZXUuYXV0aDAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTczNjUzMjg3NiwiZXhwIjoxNzM2NjE5Mjc2LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG9mZmxpbmVfYWNjZXNzIiwiYXpwIjoiS3p2MkRNS0RzRnJ1dTFibmpNZzVRazVZRGJMQnRNSnYiLCJndHkiOiJwYXNzd29yZCJ9.t6hjnJcbuiS8YWovP0vWD6OdXBCF9E8Xg29rjOMLCEKu9-ujHOlCmIQEayIDxOy5aHs3tU4q3x2cLu6oNDvzCg0bSu8K3HzJzppKnJfIjddBj2dCwJrXJVTbtfQBWHFcHTlE7-hYj9TXUJJrDaaNhtQxQQB8L5a9YVCJwzZRqJJCyiO0xZrMhBZkJb0L_xf2kl-jCa_rN2L8Z8q0pDayYfW4O_JzagIGlHXQaT7Wo_jPFOBZR6xRkVsYJBWJlVqA6_Z_XeXPzG2vJuSh88ZG1ypN5xvwzIGJBwrnvB5zl2hGQJFRJJlP6ZIoL-qB45VKruxdKOmRzVMD_Q6bOxJu4g%22%2C%22refreshToken%22%3A%22v1.MdJoCRSxdkW3e0ZqNQg1Sz0FhtLF2bDUHfVHJEzMwYJCpMPCCFdRzl4BuUbuD5-QzYZK5IBFG6MqzqnSyT7cFkg%22%2C%22idToken%22%3A%22eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjJIaDl2SlFoS1RTbGYxdFVBS2oybyJ9.eyJuaWNrbmFtZSI6ImRpZ2l0YWxob3VzZWZyIiwibmFtZSI6ImRpZ2l0YWxob3VzZWZyQHByb3Rvbi5tZSIsInBpY3R1cmUiOiJodHRwczovL3MuZ3JhdmF0YXIuY29tL2F2YXRhci9mZGJkN2Q2NDg2Mjc1YzMyMDBhODE0Mjc1N2UzOTI0OT9zPTQ4MCZyPXBnJmQ9aHR0cHMlM0ElMkYlMkZjZG4uYXV0aDAuY29tJTJGYXZhdGFycyUyRmRpLnBuZyIsInVwZGF0ZWRfYXQiOiIyMDI1LTAxLTEwVDE5OjM0OjM2LjE0OFoiLCJlbWFpbCI6ImRpZ2l0YWxob3VzZWZyQHByb3Rvbi5tZSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczovL3N3YXBjYXJkLmV1LmF1dGgwLmNvbS8iLCJhdWQiOiJLenYyRE1LRHNGcnV1MWJuak1nNVFrNVlEYkxCdE1KdiIsImlhdCI6MTczNjUzMjg3NiwiZXhwIjoxNzM2NTY4ODc2LCJzdWIiOiJhdXRoMHw2NzZjN2Y0MDlkMDIzMzg5ZjJhNGE3YzciLCJhdXRoX3RpbWUiOjE3MzY1MzI4NzYsInNpZCI6InhjNVJPX2h5bW1kaFhrT3lZZE5KT05lN25CUFZ0WW1UIiwibm9uY2UiOiJJNWpMSDJ3b2o2Q0Y5R2d5X1c2WlNOT2g4NXBKbnQyZXp1bFpNaHJ2VGVJIn0.L3xWcYEqMzcrq9Js2NUiNDFMLjwJz8MuCxLc0gGzaD4vUrruA1N-jKAbXSdPhMc2H7lSrqEy9xQBEXq4_LXCy8k2q4U8pHf5wJQRCT4e5NTk0CQ-JdJHb4IaVCsASG4-UtsjF4Qeq64zGqn9KRD_R-0a98Ft2kMdUh1c4zSKBvzPvSJUhcqW2N5x81nYB9BPz4EVJOYPIrXQdJP6gWvMu3vVsrRJSUCzb7oeRmzVcQoNDDRtpzE8IG0fHArT-WfDy0llRfN4MlpORjxD3hzBJOg7OEVr3EKJnB-j4Ae7m4r1nfh5fQqPTnsBJqCq9-aJJM25qnBGbOQ2-aOzQbSDJA%22%2C%22expiresAt%22%3A1736619276000%7D'
}

# Old headers (for scrape_all_attendees_complete.py)
OLD_HEADERS = {
    'authority': 'app.swapcard.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://app.swapcard.com',
    'referer': f'https://app.swapcard.com/event/{EVENT_SLUG}/people/{VIEW_ID}',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
}

# Rate limiting configuration
DEFAULT_WORKERS = 5
DEFAULT_DELAY_SECONDS = 0.5
DEFAULT_REQUESTS_PER_SECOND = 2.0

# File paths
DATA_DIR = 'data'
CSV_DIR = 'data/csv'
CHECKPOINT_DIR = 'data/checkpoints'
OLD_DIR = 'old'

# Output files
ATTENDEES_JSON = 'data/all_attendees_final.json'
ATTENDEES_CSV = 'data/csv/all_attendees_final.csv'
ATTENDEES_WITH_DETAILS_JSON = 'data/all_attendees_with_details.json'
ATTENDEES_WITH_DETAILS_CSV = 'data/csv/all_attendees_with_details.csv'
ATTENDEES_ORGANIZED_CSV = 'data/csv/all_attendees_with_details_organized.csv'
