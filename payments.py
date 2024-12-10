import stripe
from flask import Flask, request, jsonify

stripe.api_key = "sk_test_51QRhfsLEpW261ZratYfN5s381xLKgyMeyDWQHwNKuIPSSqFMYAUE6Ab31d1J97Pf84q2B3UKJl1dgmc6OjT7qv7f00gsPWLiGH"  # Replace with your Stripe secret key

def create_payment_intent(amount, currency='usd'):
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method_types=['card'],
        )
        return intent
    except Exception as e:
        return str(e)

def create_app():
    app = Flask(__name__)

    @app.route('/create-payment-intent', methods=['POST'])
    def create_payment():
        data = request.get_json()
        amount = data.get('amount')

        intent = create_payment_intent(amount)
        return jsonify(intent)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
