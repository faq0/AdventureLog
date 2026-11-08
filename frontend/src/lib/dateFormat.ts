export type DateFormatPreference = 'locale' | 'mdy' | 'dmy' | 'ymd';

export const DEFAULT_DATE_FORMAT: DateFormatPreference = 'locale';

export const DATE_FORMAT_OPTIONS: DateFormatPreference[] = ['locale', 'mdy', 'dmy', 'ymd'];

export const DATE_FORMAT_LABELS: Record<DateFormatPreference, string> = {
	locale: 'Browser default',
	mdy: 'MM/DD/YYYY',
	dmy: 'DD/MM/YYYY',
	ymd: 'YYYY-MM-DD'
};

const PREFERENCE_LOCALES: Record<Exclude<DateFormatPreference, 'locale'>, string> = {
	mdy: 'en-US',
	dmy: 'en-GB',
	ymd: 'sv-SE' // ISO-like YYYY-MM-DD
};

function isDateFormatPreference(value: unknown): value is DateFormatPreference {
	return typeof value === 'string' && DATE_FORMAT_OPTIONS.includes(value as DateFormatPreference);
}

export function normalizeDateFormat(value: unknown): DateFormatPreference {
	return isDateFormatPreference(value) ? value : DEFAULT_DATE_FORMAT;
}

/** Resolve an Intl locale tag for the given preference. */
export function resolveDateFormatLocale(
	preference: DateFormatPreference = DEFAULT_DATE_FORMAT
): string {
	if (preference === 'locale') {
		if (typeof navigator !== 'undefined' && navigator.language) {
			return navigator.language;
		}
		return 'en-US';
	}
	return PREFERENCE_LOCALES[preference];
}

export function prefersHour12(_preference: DateFormatPreference = DEFAULT_DATE_FORMAT): boolean {
	return false;
}

/** Format a clock time using 24-hour notation and the preferred date locale. */
export function formatDisplayTime(
	time: string | null | undefined,
	preference: DateFormatPreference = DEFAULT_DATE_FORMAT
): string {
	if (!time) return '';
	const match = /^(\d{1,2}):(\d{2})/.exec(time);
	if (!match) return time;
	const hours = Number(match[1]);
	const minutes = Number(match[2]);
	if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return time;

	const date = new Date(2000, 0, 1, hours, minutes);
	try {
		return new Intl.DateTimeFormat(resolveDateFormatLocale(preference), {
			hour: '2-digit',
			minute: '2-digit',
			hourCycle: 'h23'
		}).format(date);
	} catch {
		return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
	}
}

function parseDateOnly(iso: string): Date | null {
	if (!iso) return null;
	const datePart = iso.split('T')[0];
	if (!/^\d{4}-\d{2}-\d{2}$/.test(datePart)) return null;
	// Midday avoids DST/timezone day-shift for date-only values
	return new Date(`${datePart}T12:00:00`);
}

export type FormatDisplayDateOptions = {
	/** Force UTC for date-only calendar fields (notes/checklists). */
	timeZone?: string;
	month?: 'numeric' | '2-digit' | 'short' | 'long';
	year?: 'numeric' | '2-digit';
	day?: 'numeric' | '2-digit';
};

/** Format a date-only ISO string (YYYY-MM-DD or datetime truncated to date). */
export function formatDisplayDate(
	iso: string | null | undefined,
	preference: DateFormatPreference = DEFAULT_DATE_FORMAT,
	opts: FormatDisplayDateOptions = {}
): string {
	if (!iso) return '';
	const date = parseDateOnly(iso);
	if (!date || Number.isNaN(date.getTime())) return '';

	const locale = resolveDateFormatLocale(preference);
	try {
		return new Intl.DateTimeFormat(locale, {
			year: opts.year ?? 'numeric',
			month: opts.month ?? (preference === 'ymd' ? '2-digit' : 'short'),
			day: opts.day ?? (preference === 'ymd' ? '2-digit' : 'numeric'),
			timeZone: opts.timeZone
		}).format(date);
	} catch {
		return date.toLocaleDateString();
	}
}

/** Format a UTC datetime ISO string with optional timezone. */
export function formatDisplayDateTime(
	iso: string | null | undefined,
	preference: DateFormatPreference = DEFAULT_DATE_FORMAT,
	timezone?: string | null
): string {
	if (!iso) return '';
	try {
		const locale = resolveDateFormatLocale(preference);
		return new Intl.DateTimeFormat(locale, {
			timeZone: timezone || undefined,
			year: 'numeric',
			month: preference === 'ymd' ? '2-digit' : 'short',
			day: preference === 'ymd' ? '2-digit' : 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			hourCycle: 'h23'
		}).format(new Date(iso));
	} catch {
		return new Date(iso).toLocaleString();
	}
}

/**
 * First day of week for Cally: 0 = Sunday, 1 = Monday.
 * `locale` preference uses Intl.Locale weekInfo when available.
 */
export function getFirstDayOfWeek(preference: DateFormatPreference = DEFAULT_DATE_FORMAT): number {
	if (preference === 'mdy') return 0;
	if (preference === 'dmy' || preference === 'ymd') return 1;

	try {
		const localeTag = resolveDateFormatLocale(preference);
		const locale = new Intl.Locale(localeTag) as Intl.Locale & {
			weekInfo?: { firstDay?: number };
			getWeekInfo?: () => { firstDay?: number };
		};
		const info = locale.weekInfo ?? locale.getWeekInfo?.();
		// Intl uses 1=Monday … 7=Sunday; Cally uses 0=Sunday … 6=Saturday
		if (info?.firstDay != null) {
			return info.firstDay === 7 ? 0 : info.firstDay;
		}
	} catch {
		// fall through
	}
	return 1;
}

/** Preview string for settings UI (today in the chosen format). */
export function formatDateFormatPreview(preference: DateFormatPreference): string {
	const today = new Date();
	const iso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
	return formatDisplayDate(iso, preference, { month: '2-digit', day: '2-digit', year: 'numeric' });
}

/** Normalize preference from a user object (or guests). */
export function dateFormatFromUser(
	user: { date_format?: string } | null | undefined
): DateFormatPreference {
	return normalizeDateFormat(user?.date_format);
}

/** Numeric date entry follows the user's date order; ISO is accepted everywhere. */
export function dateInputFormat(preference: DateFormatPreference): 'mdy' | 'dmy' | 'ymd' {
	if (preference !== 'locale') return preference;
	const parts = new Intl.DateTimeFormat(resolveDateFormatLocale(preference)).formatToParts(
		new Date(2024, 10, 23)
	);
	const first = parts.find((part) => ['year', 'month', 'day'].includes(part.type))?.type;
	return first === 'year' ? 'ymd' : first === 'day' ? 'dmy' : 'mdy';
}

export function dateInputPlaceholder(preference: DateFormatPreference): string {
	return { mdy: 'MM/DD/YYYY', dmy: 'DD/MM/YYYY', ymd: 'YYYY-MM-DD' }[dateInputFormat(preference)];
}

export function formatDateInput(iso: string, preference: DateFormatPreference): string {
	if (!iso) return '';
	const [year, month, day] = iso.split('T')[0].split('-');
	if (!year || !month || !day) return '';
	const order = dateInputFormat(preference);
	return order === 'ymd'
		? `${year}-${month}-${day}`
		: order === 'dmy'
			? `${day}/${month}/${year}`
			: `${month}/${day}/${year}`;
}

export function parseDateInput(text: string, preference: DateFormatPreference): string | null {
	const parts = text.trim().split(/[./-]/);
	if (parts.length !== 3 || parts.some((part) => !/^\d+$/.test(part))) return null;
	const order = /^\d{4}[/-]/.test(text.trim()) ? 'ymd' : dateInputFormat(preference);
	const [year, month, day] =
		order === 'ymd'
			? [parts[0], parts[1], parts[2]]
			: order === 'dmy'
				? [parts[2], parts[1], parts[0]]
				: [parts[2], parts[0], parts[1]];
	if (year.length !== 4 || month.length > 2 || day.length > 2 || Number(year) < 1) return null;
	const date = new Date(0);
	date.setUTCFullYear(Number(year), Number(month) - 1, Number(day));
	if (
		date.getUTCFullYear() !== Number(year) ||
		date.getUTCMonth() !== Number(month) - 1 ||
		date.getUTCDate() !== Number(day)
	)
		return null;
	return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

export function parseTimeInput(text: string): string | null {
	const match = /^(\d{1,2}):(\d{2})$/.exec(text.trim());
	if (!match || Number(match[1]) > 23 || Number(match[2]) > 59) return null;
	return `${match[1].padStart(2, '0')}:${match[2]}`;
}
