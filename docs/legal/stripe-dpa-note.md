# Stripe DPA & go-live checklist (non-legal)

1. Sign Stripe's **Data Processing Agreement** in Dashboard -> Settings -> Legal.  
2. Keep billing minimal for pilot: one product/price in Stripe, no Tax/invoice/dunning workflows in this repo.  
3. Configure **Customer portal** branding + return URL (`STRIPE_CUSTOMER_PORTAL_RETURN_URL`).  
4. Webhooks (MVP): subscribe to `checkout.session.completed` and `customer.subscription.*` only - see `app/api/v1/billing.py`. Add `invoice.*` later if you enable invoicing/dunning.  
5. Test with **Stripe CLI** forwarding to `/api/v1/billing/webhook`.  

Counsel should review MSA, pricing, and tax nexus.
