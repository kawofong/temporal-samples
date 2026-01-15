package io.temporal.samples.expirableWorkflow;

/** Input for the expirable payment workflow. */
public class PaymentWorkflowInput {

  private String paymentId;
  private double amount;

  /** Number of seconds until the workflow expires. */
  private int expireIn;

  /** Default constructor required for serialization. */
  public PaymentWorkflowInput() {}

  public PaymentWorkflowInput(String paymentId, double amount, int expireIn) {
    this.paymentId = paymentId;
    this.amount = amount;
    this.expireIn = expireIn;
  }

  public String getPaymentId() {
    return paymentId;
  }

  public void setPaymentId(String paymentId) {
    this.paymentId = paymentId;
  }

  public double getAmount() {
    return amount;
  }

  public void setAmount(double amount) {
    this.amount = amount;
  }

  public int getExpireIn() {
    return expireIn;
  }

  public void setExpireIn(int expireIn) {
    this.expireIn = expireIn;
  }
}
