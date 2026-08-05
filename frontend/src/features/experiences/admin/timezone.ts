interface WallClockParts {
  day: number;
  hour: number;
  minute: number;
  month: number;
  year: number;
}

function partsAt(instant: Date, timezone: string): WallClockParts {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    day: "2-digit",
    hour: "2-digit",
    hourCycle: "h23",
    minute: "2-digit",
    month: "2-digit",
    timeZone: timezone,
    year: "numeric",
  });
  const values = Object.fromEntries(
    formatter
      .formatToParts(instant)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, Number(part.value)]),
  );
  return {
    day: values.day ?? 0,
    hour: values.hour ?? 0,
    minute: values.minute ?? 0,
    month: values.month ?? 0,
    year: values.year ?? 0,
  };
}

function sameParts(left: WallClockParts, right: WallClockParts): boolean {
  return (
    left.year === right.year &&
    left.month === right.month &&
    left.day === right.day &&
    left.hour === right.hour &&
    left.minute === right.minute
  );
}

export function zonedLocalToUtc(value: string, timezone: string): Date {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/u.exec(value);
  if (!match) throw new Error("Enter a complete local date and time.");
  const target: WallClockParts = {
    year: Number(match[1]),
    month: Number(match[2]),
    day: Number(match[3]),
    hour: Number(match[4]),
    minute: Number(match[5]),
  };
  const wallAsUtc = Date.UTC(target.year, target.month - 1, target.day, target.hour, target.minute);
  const offsets = new Set<number>();
  for (const delta of [-36, -12, 0, 12, 36]) {
    const probe = new Date(wallAsUtc + delta * 60 * 60 * 1000);
    const parts = partsAt(probe, timezone);
    offsets.add(
      Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute) - probe.getTime(),
    );
  }
  const matches = [...offsets]
    .map((offset) => new Date(wallAsUtc - offset))
    .filter((candidate) => sameParts(partsAt(candidate, timezone), target));
  if (matches.length === 0) {
    throw new Error("That local time does not exist in the configured timezone.");
  }
  if (matches.length > 1) {
    throw new Error("That local time is ambiguous in the configured timezone.");
  }
  return matches[0] as Date;
}

export function formatInTimezone(value: Date, timezone: string): string {
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    timeZone: timezone,
    timeZoneName: "short",
    year: "numeric",
  }).format(value);
}
