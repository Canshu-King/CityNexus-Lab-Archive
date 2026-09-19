
  const accept = async (proposalId: string) => {
    setBusy(proposalId);
    setMessage(null);
    try {
      const r = await fetch(`/api/v1/replans/${proposalId}/accept`, {
        method: "POST",
        headers: { "Idempotency-Key": `accept-${proposalId}` },
      });
      if (!r.ok) {
        const body = await r.json().catch(() => null);
        setMessage(
          body?.error?.message ??
            body?.detail ??
            (zh ? "暂时无法接受这个调整。" : "Could not accept this change."),
        );
        return;
      }
      setMessage(zh ? "已按新安排更新你的行程。" : "Your trip has been updated.");
      await loadProposals();
      await plans.refetch();
      await twin.refetch();
      onAccepted?.();
    } catch {
      setMessage(zh ? "连不上服务器，请重试。" : "Could not reach the server. Try again.");
    } finally {
      setBusy(null);
    }
  };

  const defer = () =>
    setMessage(zh ? "好的，稍后再提醒你。" : "Okay, we will remind you later.");

  return (
    <section className="v8-page" data-testid="live-recovery">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{zh ? "正在进行" : "In progress"}</p>
          <h1>{zh ? "现在的行程" : "Your trip right now"}</h1>
          <p className="v8-lede" data-testid="live-next">
            {liveNow
              ? zh
                ? `下一站：${String(liveNow.title ?? "")}`
                : `Next: ${String(liveNow.title ?? "")}`
              : zh
                ? "还没有选定的行程安排。"
                : "No plan is active yet."}
          </p>
        </div>
      </div>
