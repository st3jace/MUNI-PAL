# Muni-Pal payment verification

September 17, 2026 — Launch Shop Stripe **test mode**

The deployed portal completed a simulated $10 payment and full refund. No real
funds moved. Real customer payments are not enabled yet.

| Check | Result |
|---|---|
| Declined card | Payment rejected; report remains locked |
| Successful card | Payment accepted; report generation and download unlocked |
| Another client's access | Denied |
| Repeated checkout request | Reused the same session |
| $2 partial refund | Report access preserved |
| Remaining $8 refunded | Generation and downloads blocked |
| Old payment notification replayed after refund | Access remained blocked |
| Separate subscription access | Not granted by the deal purchase |

The hosted test exposed a Stripe library compatibility bug in the notification
handler. The fix is deployed and covered by real-signature regression tests.
All 28 focused payment/portal integration tests passed.

Two test report versions were saved. Both temporary test accounts are now inactive;
the clearly labeled test deal remains in the operator workspace for reference.

- [Test payment and refund](https://dashboard.stripe.com/acct_19wrEUFDH0RHRrjH/test/payments/pi_3UGpIQFDH0RHRrjH0vRcIzXE)
- [Payment notification deliveries](https://dashboard.stripe.com/acct_19wrEUFDH0RHRrjH/test/workbench/webhooks/we_1UGokGFDH0RHRrjHlWK9ML3E/events)
- [Code review](https://github.com/st3jace/MUNI-PAL/pull/1)
- [Client portal](https://muni-pal.io/register)

Before paid onboarding: configure live Stripe credentials and a separate live
webhook, set up backups and retention, and complete the remaining release checks
in the project launch notes. Card flows were tested against Stripe; delayed payment
methods and expiration were covered in automated tests only.
