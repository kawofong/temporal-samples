package io.temporal.samples.expirableWorkflow;

/** Result of the expirable payment workflow. */
public class PaymentWorkflowResult {

  private String paymentId;
  private PaymentStatus status;
  private String message;

  /** Default constructor required for serialization. */
  public PaymentWorkflowResult() {}

  public PaymentWorkflowResult(String paymentId, PaymentStatus status, String message) {
    this.paymentId = paymentId;
    this.status = status;
    this.message = message;
  }

  public String getPaymentId() {
    return paymentId;
  }

  public void setPaymentId(String paymentId) {
    this.paymentId = paymentId;
  }

  public PaymentStatus getStatus() {
    return status;
  }

  public void setStatus(PaymentStatus status) {
    this.status = status;
  }

  public String getMessage() {
    return message;
  }

  public void setMessage(String message) {
    this.message = message;
  }

  @Override
  public String toString() {
    return "PaymentWorkflowResult{"
        + "paymentId='"
        + paymentId
        + '\''
        + ", status="
        + status
        + ", message='"
        + message
        + '\''
        + '}';
  }
}
