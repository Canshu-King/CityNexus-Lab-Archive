
export function LiveRecovery({
  journeyId,
  onAccepted,
}: {
  journeyId: string;
  onAccepted?: () => void;
}) {
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");
  const twin = useAuthoritativeTwin(journeyId);
  const plans = useAuthoritativePlans(journeyId);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadProposals = useCallback(async () => {
    try {
      const r = await fetch(`/api/v1/journeys/${journeyId}/replans`);
      const body = await r.json();
      setProposals(Array.isArray(body) ? (body as Proposal[]) : []);
    } catch {
      setProposals([]);
    }
  }, [journeyId]);

  useEffect(() => {
    void loadProposals();
  }, [loadProposals]);

  const plan =
    plans.data?.find((p) => p.status === "ACTIVE" || p.status === "SELECTED") ?? null;
  const activities = (plan?.activities ?? []) as unknown as Array<Record<string, unknown>>;
  const context = twin.data?.context as
    | { disruptions?: Disruption[]; execution?: { current_activity_id?: string | null } }
    | undefined;
  const disruptions = (context?.disruptions ?? []) as Disruption[];
  const pending = proposals.filter(
    (p) => p.status === "PRESENTED" || p.status === "GENERATED",
  );
  const currentId = context?.execution?.current_activity_id ?? null;
  const liveNow =
    activities.find((a) => a.id === currentId) ?? activities[0] ?? null;
