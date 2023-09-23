function makeSubscription(stripe_publishable_key, customer_email, clientSecret, price_id, redirect_url) {
    document.addEventListener("DOMContentLoader", function(event) {
        const stripe = Stripe(stripe_publishable_key);
        
        // Set up Stripe.js and Elements to use in checkout form
        const elements = stripe.elements({"clientSecret": clientSecret});
        
        // Create and mount the Card Element
        const cardElement = elements.create('card');
        cardElement.mount('#card-element');
        
        var form = document.getElementById('card-form');
        const submitBtn = document.getElementById('submit_btn');
        
        const handleError = (error) => {
          const messageContainer = document.querySelector('#stripe-error_msg');
          messageContainer.textContent = error.message;
          submitBtn.disabled = false;
        }
        
        cardElement.addEventListener('change', function(event) => {
          if (event.error) {
            handleError(event.error);
          }
        });
        
        form.addEventListener('submit', async (event) => {
          // We don't want to let default form submission happen here,
          // which would refresh the page.
          event.preventDefault();
        
          // Prevent multiple form submissions
          if (submitBtn.disabled) {
            return;
          }
        
          // Disable form submission while loading
          submitBtn.disabled = true;
        
          stripe.createToken(cardElement).then(function(event) {
              if (event.error) {
                  handleError(event.error);
              } else {
                  // Create payment method
                  stripe.createPaymentMethod({
                      type: "card",
                      card: card,
                      billing_details: {
                          email: customer_email,
                      }
                  }).then(function(payment_method_result) {
                      if (payment_method_result.error) {
                          handleError(payment_method_result.error);
                      } else {
                          
                          // Create the subscription
                          const res = await fetch('/finances/pricing/'+price_id+'/payment/', {
                            method: "POST",
                            body: JSON.stringify({
                                payment_method_id: payment_method_result.paymentMethod.id,
                            }),
                          });
                          const data = await res.json();
                          const type = data["type"]
                          const clientSecret = data["clientSecret"]
                        
                          // Confirm card payment with an existing payment method 
                          
                          stripe.confirmCardPayment(clientSecret, {
                            payment_method: payment_method_result.paymentMethod.id,
                            return_url: return_url
                          })
                          .then(function(result) {
                            // Handle result.error or result.paymentIntent
                            if (result.error) {
                                handleError(error);
                            }
                          });
                          
                          
                      }
                  })
              }
          })
        
        });
        
    })
}