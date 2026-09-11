import stripe
from stripe import error

def test_stripe_key():
    stripe_secret_key = input("Enter your Stripe secret key: ")
    stripe.api_key = stripe_secret_key

    try:
        account = stripe.Account.retrieve()

        print("\n━━━━━「 ACCOUNT DETAILS 」━━━━━")
        print(f"⎔ ID: {account.id}")
        print(f"⎔ Email: {getattr(account, 'email', 'Not available')}")
        print(f"⎔ Country: {account.country}")
        print(f"⎔ Default Currency: {account.default_currency.upper()}")
        print(f"⎔ Account Type: {getattr(account, 'type', 'Not available')}")
        
        # Charges & Payouts
        print("\n━━━━━「 STATUS 」━━━━━")
        print(f"⎔ Charges Enabled: {'Yes ✅' if account.charges_enabled else 'No ❌'}")
        print(f"⎔ Payouts Enabled: {'Yes ✅' if account.payouts_enabled else 'No ❌'}")
        print(f"⎔ Integration Status: {'Active ✅' if account.details_submitted else 'Inactive ❌'}")

        # Capabilities
        print("\n━━━━━「 CAPABILITIES 」━━━━━")
        if hasattr(account, 'capabilities'):
            for cap, status in account.capabilities.items():
                print(f"⎔ {cap.replace('_', ' ').title()}: {'Active ✅' if status == 'active' else 'Inactive ❌'}")
        else:
            print("⎔ No capabilities found")

        # Balance
        balance = stripe.Balance.retrieve()
        print("\n━━━━━「 BALANCE 」━━━━━")
        for item in balance.available:
            print(f"⎔ Available: {item.amount / 100} {item.currency.upper()}")
        for item in balance.pending:
            print(f"⎔ Pending: {item.amount / 100} {item.currency.upper()}")

        # Payment Test
        print("\n━━━━━「 PAYMENT TEST 」━━━━━")
        test_card_payment(stripe_secret_key)

    except error.AuthenticationError:
        print("Invalid Stripe secret key ❌")
    except error.StripeError as e:
        print(f"Error: {e}")

def test_card_payment(api_key):
    stripe.api_key = api_key
    try:
        # Card details (DELETE AFTER TESTING!)
        card = {
            "number": "5423589113745376",
            "exp_month": "08",
            "exp_year": "2027",
            "cvc": "550"
        }

        # Create payment token
        token = stripe.Token.create(card=card)
        
        # Create charge
        charge = stripe.Charge.create(
            amount=100,  # $1.00
            currency="usd",
            source=token.id,
            description="SK Tester Validation Charge"
        )

        # Print charge details
        print(f"⎔ Charge ID: {charge.id}")
        print(f"⎔ Amount: ${charge.amount/100:.2f} {charge.currency.upper()}")
        print(f"⎔ Status: {charge.status.upper()} ✅")
        print(f"⎔ Payment Method: {charge.payment_method_details.card.brand.upper()}")
        print(f"⎔ Card Last4: **** **** **** {charge.payment_method_details.card.last4}")
        print(f"⎔ Receipt URL: {charge.receipt_url}")
        print("⎔ Payment Successful! ✅")

    except error.CardError as e:
        print(f"⎔ Card Declined ❌")
        print(f"⎔ Error Code: {e.code}")
        print(f"⎔ Decline Reason: {e.error.message}")
    except error.StripeError as e:
        print(f"⎔ Payment Error: {e.user_message} ❌")

if __name__ == "__main__":
    test_stripe_key()