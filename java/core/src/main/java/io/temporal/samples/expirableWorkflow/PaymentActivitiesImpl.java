package io.temporal.samples.expirableWorkflow;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Implementation of payment processing activities. */
public class PaymentActivitiesImpl implements PaymentActivities {

  private static final Logger logger = LoggerFactory.getLogger(PaymentActivitiesImpl.class);

  @Override
  public boolean validatePayment(String paymentId, double amount) {
    logger.info("Validating payment. paymentId={}, amount={}", paymentId, amount);
    // Simulate validation processing time
    sleep(1000);

    // Simulate validation logic (in real world, check card details, balance, etc.)
    boolean isValid = amount > 0 && amount < 10000;
    logger.info("Payment validation complete. paymentId={}, isValid={}", paymentId, isValid);
    return isValid;
  }

  @Override
  public boolean checkFraud(String paymentId, double amount) {
    logger.info("Checking for fraud. paymentId={}, amount={}", paymentId, amount);
    // Simulate fraud check processing time
    sleep(1000);

    // Simulate fraud detection (in real world, use ML models, rules, etc.)
    boolean isFraudulent = amount > 5000; // Simple rule: flag large amounts
    logger.info("Fraud check complete. paymentId={}, isFraudulent={}", paymentId, isFraudulent);
    return !isFraudulent; // Return true if NOT fraudulent
  }

  @Override
  public String acceptPayment(String paymentId, double amount) {
    logger.info("Accepting payment. paymentId={}, amount={}", paymentId, amount);
    // Simulate payment processing time
    sleep(1000);

    // Generate a transaction ID
    String transactionId = "TXN-" + paymentId + "-" + (int) (amount * 100);
    logger.info("Payment accepted. paymentId={}, transactionId={}", paymentId, transactionId);
    return transactionId;
  }

  @Override
  public void notifyCustomer(String paymentId, String transactionId) {
    logger.info("Notifying customer. paymentId={}, transactionId={}", paymentId, transactionId);
    // Simulate notification sending time
    sleep(1000);

    logger.info(
        "Customer notified successfully. paymentId={}, transactionId={}", paymentId, transactionId);
  }

  private void sleep(long millis) {
    try {
      Thread.sleep(millis);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new RuntimeException("Activity interrupted", e);
    }
  }
}
