import csv
import requests
from collections import Counter

API_URL = "http://localhost:8000/triage"

def to_bool(x) -> bool:
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in ("true", "1", "yes", "y")

def norm_label(s: str) -> str:
    return (s or "").strip().lower()

def main():
    with open("eval/golden_set.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    n_total = len(rows)
    if n_total == 0:
        print("No rows found in eval/golden_set.csv")
        return

    y_intent_true, y_intent_pred = [], []
    y_esc_true, y_esc_pred = [], []
    unsafe_auto = 0
    n_failed = 0

    for r in rows:
        payload = {
            "conversation_id": r.get("conversation_id"),
            "transcript": r.get("transcript"),
            "metadata": {"channel": "eval"}
        }

        resp = None
        try:
            resp = requests.post(API_URL, json=payload, timeout=120)
            resp.raise_for_status()
            pred = resp.json()
        except Exception as e:
            n_failed += 1
            print("\n--- REQUEST FAILED ---")
            print("conversation_id:", r.get("conversation_id"))
            print("error:", repr(e))
            if resp is not None:
                print("status:", getattr(resp, "status_code", None))
                body = getattr(resp, "text", "")
                if body:
                    print("body:", body[:500])
            continue

        true_intent = norm_label(r.get("true_intent"))
        true_escalate = to_bool(r.get("should_escalate"))

        pred_intent = norm_label(pred.get("intent"))
        pred_escalate = to_bool(pred.get("escalate", False))

        y_intent_true.append(true_intent)
        y_intent_pred.append(pred_intent)

        y_esc_true.append(true_escalate)
        y_esc_pred.append(pred_escalate)

        if true_escalate and (not pred_escalate):
            unsafe_auto += 1

    n_ok = len(y_esc_true)
    if n_ok == 0:
        print("All requests failed; no metrics to report.")
        print(f"Total rows: {n_total}, Failed: {n_failed}")
        return

    # Intent accuracy
    intent_correct = sum(1 for t, p in zip(y_intent_true, y_intent_pred) if t == p)
    intent_acc = intent_correct / n_ok

    # Escalation confusion matrix
    tp = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if t and p)
    tn = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if (not t) and (not p))
    fp = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if (not t) and p)
    fn = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if t and (not p))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    positives = tp + fn
    unsafe_rate = (unsafe_auto / positives) if positives else 0.0

    print("\n=== EVALUATION RESULTS ===")
    print(f"Total rows: {n_total}")
    print(f"Successful: {n_ok}")
    print(f"Failed: {n_failed}")

    print(f"\nIntent accuracy: {intent_acc:.2%} ({intent_correct}/{n_ok})")

    print(f"\nEscalation precision: {precision:.2%} (TP={tp}, FP={fp})")
    print(f"Escalation recall: {recall:.2%} (TP={tp}, FN={fn})")
    print(f"Escalation F1: {f1:.2%}")
    print(f"Unsafe auto-resolve (FN): {unsafe_auto} (rate={unsafe_rate:.2%} of true-escalations)")
    print(f"Escalation confusion: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    print("\nPredicted intent distribution:")
    for k, v in Counter(y_intent_pred).most_common():
        print(f"  {k or '<empty>'}: {v}")

if __name__ == "__main__":
    main()




# import csv
# import requests
# from collections import Counter

# API_URL = "http://localhost:8000/triage"

# def to_bool(x: str) -> bool:
#     return str(x).strip().lower() in ("true", "1", "yes", "y")

# def main():
#     with open("eval/golden_set.csv", newline="", encoding="utf-8") as f:
#         rows = list(csv.DictReader(f))

#     total = len(rows)
#     if total == 0:
#         print("No rows found in eval/golden_set.csv")
#         return

#     y_intent_true, y_intent_pred = [], []
#     y_esc_true, y_esc_pred = [], []
#     unsafe_auto = 0

#     for r in rows:
#         payload = {
#             "conversation_id": r["conversation_id"],
#             "transcript": r["transcript"],
#             "metadata": {"channel": "eval"}
#         }

#         try:
#             resp = requests.post(API_URL, json=payload, timeout=120)
#             resp.raise_for_status()
#             pred = resp.json()
#         except Exception as e:
#             print("\n--- REQUEST FAILED ---")
#             print("conversation_id:", r["conversation_id"])
#             print("transcript:", r["transcript"])
#             try:
#                 print("status:", resp.status_code)
#                 print("body:", resp.text[:500])
#             except:
#                 pass
#             print("error:", repr(e))
#             continue

#         true_intent = r["true_intent"].strip()
#         true_escalate = to_bool(r["should_escalate"])

#         pred_intent = (pred.get("intent") or "").strip()
#         pred_escalate = bool(pred.get("escalate", False))

#         y_intent_true.append(true_intent)
#         y_intent_pred.append(pred_intent)

#         y_esc_true.append(true_escalate)
#         y_esc_pred.append(pred_escalate)

#         if true_escalate and (not pred_escalate):
#             unsafe_auto += 1


#     # Intent accuracy
#     intent_correct = sum(1 for t, p in zip(y_intent_true, y_intent_pred) if t == p)
#     intent_acc = intent_correct / total

#     # Escalation confusion matrix
#     tp = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if t and p)
#     tn = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if (not t) and (not p))
#     fp = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if (not t) and p)
#     fn = sum(1 for t, p in zip(y_esc_true, y_esc_pred) if t and (not p))

#     precision = tp / (tp + fp) if (tp + fp) else 0
#     recall = tp / (tp + fn) if (tp + fn) else 0

#     print("\n=== EVALUATION RESULTS ===")
#     print(f"Samples: {total}")
#     print(f"Intent accuracy: {intent_acc:.2%} ({intent_correct}/{total})")
#     print(f"Escalation precision: {precision:.2%} (TP={tp}, FP={fp})")
#     print(f"Escalation recall: {recall:.2%} (TP={tp}, FN={fn})")
#     print(f"Unsafe auto-resolve (should escalate but didn't): {unsafe_auto}")
#     print(f"Escalation confusion: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

#     print("\nPredicted intent distribution:")
#     for k, v in Counter(y_intent_pred).most_common():
#         print(f"  {k}: {v}")

# if __name__ == "__main__":
#     main()

