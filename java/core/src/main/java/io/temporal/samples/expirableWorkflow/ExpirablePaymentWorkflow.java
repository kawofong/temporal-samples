package io.temporal.samples.expirableWorkflow;

import io.temporal.workflow.QueryMethod;
import io.temporal.workflow.WorkflowInterface;
import io.temporal.workflow.WorkflowMethod;

/**
 * A payment workflow that automatically cancels itself after a specified duration.
 *
 * <p>The workflow:
 *
 * <ol>
 *   <li>Starts a Timer with the expiration duration
 *   <li>In parallel, processes the payment (validate, fraud check, accept, notify)
 *   <li>If the Timer fires before payment completes, the workflow cancels itself
 * </ol>
 */
@WorkflowInterface
public interface ExpirablePaymentWorkflow {

  /** Main workflow method that processes the payment with expiration. */
  @WorkflowMethod
  PaymentWorkflowResult processPayment(PaymentWorkflowInput input);

  /** Query to get the current payment status. */
  @QueryMethod
  PaymentStatus getStatus();

  /** Query to check if the workflow has expired. */
  @QueryMethod
  boolean isExpired();
}
