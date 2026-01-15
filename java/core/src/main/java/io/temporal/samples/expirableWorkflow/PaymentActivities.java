package io.temporal.samples.expirableWorkflow;

import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

/** Payment processing activities for the expirable workflow. */
@ActivityInterface
public interface PaymentActivities {

  /** Validates the payment details. */
  @ActivityMethod
  boolean validatePayment(String paymentId, double amount);

  /** Performs fraud detection on the payment. */
  @ActivityMethod
  boolean checkFraud(String paymentId, double amount);

  /** Accepts and processes the payment. */
  @ActivityMethod
  String acceptPayment(String paymentId, double amount);

  /** Notifies the customer about the payment result. */
  @ActivityMethod
  void notifyCustomer(String paymentId, String transactionId);
}
