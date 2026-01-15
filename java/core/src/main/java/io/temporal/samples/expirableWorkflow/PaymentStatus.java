package io.temporal.samples.expirableWorkflow;

/** Payment processing status. */
public enum PaymentStatus {
  PENDING,
  VALIDATING,
  FRAUD_CHECK,
  ACCEPTED,
  NOTIFIED,
  COMPLETED,
  CANCELLED,
  EXPIRED
}
