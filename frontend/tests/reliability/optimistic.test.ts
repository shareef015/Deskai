import { beginOptimisticTransaction } from "../../src/lib/reliability/optimistic";

describe("optimistic transactions", () => {
  it("rolls back to the authoritative previous value", () => {
    let value = "open";
    const transaction = beginOptimisticTransaction("open", "resolved", (next) => { value = next; }, (previous) => { value = previous; });
    value = transaction.optimistic;
    expect(value).toBe("resolved");
    transaction.rollback();
    expect(value).toBe("open");
  });
});
