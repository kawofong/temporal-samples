package io.temporal.samples.expirableWorkflow;

import io.temporal.activity.ActivityOptions;
import io.temporal.common.RetryOptions;
import io.temporal.failure.ActivityFailure;
import io.temporal.failure.CanceledFailure;
import io.temporal.workflow.Async;
import io.temporal.workflow.CancellationScope;
import io.temporal.workflow.Promise;
import io.temporal.workflow.Workflow;
import java.time.Duration;
import org.slf4j.Logger;

/**
 * Implementation of the expirable payment workflow.
 *
 * <p>This workflow demonstrates how to implement a self-cancelling workflow that expires after a
 * specified duration using a Timer racing against the main business logic.
 */
public class ExpirablePaymentWorkflowImpl implements ExpirablePaymentWorkflow {

  private static final Logger logger = Workflow.getLogger(ExpirablePaymentWorkflowImpl.class);

  private final PaymentActivities activities =
      Workflow.newActivityStub(
          PaymentActivities.class,
          ActivityOptions.newBuilder()
              .setStartToCloseTimeout(Duration.ofSeconds(30))
              .setRetryOptions(
                  RetryOptions.newBuilder().setMaximumInterval(Duration.ofSeconds(5)).build())
              .build());

  private String paymentId;
  private double amount;
  private int expireIn;
  private PaymentStatus status = PaymentStatus.PENDING;
  private boolean expired = false;
  private PaymentWorkflowResult paymentResult;

  @Override
  public PaymentWorkflowResult processPayment(PaymentWorkflowInput input) {
    this.paymentId = input.getPaymentId();
    this.amount = input.getAmount();
    this.expireIn = input.getExpireIn();

    logger.info(
        "Starting expirable payment workflow. paymentId={}, expireIn={} seconds",
        paymentId,
        expireIn);

    // Create a cancellation scope for the payment processing
    CancellationScope paymentScope =
        Workflow.newCancellationScope(
            () -> {
              // Run payment processing asynchronously within the scope
              Promise<PaymentWorkflowResult> paymentPromise =
                  Async.function(this::processPaymentInternal);
              // Wait for payment to complete (or get cancelled)
              try {
                paymentResult = paymentPromise.get();
              } catch (CanceledFailure e) {
                // Payment was cancelled by the timer
                status = PaymentStatus.EXPIRED;
                paymentResult =
                    new PaymentWorkflowResult(paymentId, status, "Payment workflow expired");
              }
            });

    // Start the expiration timer that will cancel the payment scope when it fires
    Promise<Void> timerPromise = Workflow.newTimer(Duration.ofSeconds(expireIn));
    timerPromise.thenApply(
        result -> {
          logger.info("Expiration timer fired! paymentId={}", paymentId);
          expired = true;
          paymentScope.cancel("Workflow expired after " + expireIn + " seconds");
          return null;
        });

    // Execute the payment processing within the cancellation scope
    try {
      paymentScope.run();
    } catch (ActivityFailure e) {
      if (e.getCause() instanceof CanceledFailure) {
        expired = true;
        status = PaymentStatus.EXPIRED;
        logger.warn("Payment workflow expired. paymentId={}", paymentId);
        return new PaymentWorkflowResult(paymentId, status, "Payment workflow expired");
      }
      throw e;
    }

    // Return the result (either completed payment or expired)
    if (paymentResult != null) {
      return paymentResult;
    }

    // This shouldn't happen, but handle it gracefully
    return new PaymentWorkflowResult(paymentId, status, "Workflow completed unexpectedly");
  }

  private PaymentWorkflowResult processPaymentInternal() {
    // Step 1: Validate payment
    status = PaymentStatus.VALIDATING;
    logger.info("Step 1: Validating payment. paymentId={}", paymentId);
    boolean isValid = activities.validatePayment(paymentId, amount);

    if (!isValid) {
      status = PaymentStatus.CANCELLED;
      return new PaymentWorkflowResult(paymentId, status, "Payment validation failed");
    }

    // Step 2: Check for fraud
    status = PaymentStatus.FRAUD_CHECK;
    logger.info("Step 2: Checking for fraud. paymentId={}", paymentId);
    boolean isNotFraudulent = activities.checkFraud(paymentId, amount);

    if (!isNotFraudulent) {
      status = PaymentStatus.CANCELLED;
      return new PaymentWorkflowResult(
          paymentId, status, "Payment flagged as potentially fraudulent");
    }

    // Step 3: Accept payment
    status = PaymentStatus.ACCEPTED;
    logger.info("Step 3: Accepting payment. paymentId={}", paymentId);
    String transactionId = activities.acceptPayment(paymentId, amount);

    // Step 4: Notify customer
    status = PaymentStatus.NOTIFIED;
    logger.info("Step 4: Notifying customer. paymentId={}", paymentId);
    activities.notifyCustomer(paymentId, transactionId);

    // Complete
    status = PaymentStatus.COMPLETED;
    logger.info(
        "Payment workflow completed successfully. paymentId={}, transactionId={}",
        paymentId,
        transactionId);

    return new PaymentWorkflowResult(
        paymentId, status, "Payment completed successfully. Transaction ID: " + transactionId);
  }

  @Override
  public PaymentStatus getStatus() {
    return status;
  }

  @Override
  public boolean isExpired() {
    return expired;
  }
}
