<script lang="ts">
	import { onMount } from 'svelte';
	import type { Attachment } from 'svelte/attachments';
	import { page } from '$app/state';
	import CalendarIcon from '~icons/mdi/calendar';
	import ClockIcon from '~icons/mdi/clock-outline';
	import CloseIcon from '~icons/mdi/close';
	import {
		normalizeDateFormat,
		formatDateInput,
		parseDateInput,
		parseTimeInput,
		dateInputPlaceholder,
		getFirstDayOfWeek,
		resolveDateFormatLocale
	} from '#lib/dateFormat.js';
	import { attachPopoverFlip } from '#lib/utils/flipDropdown.js';

	interface Props {
		value?: string | null;
		label?: string;
		id?: string;
		name?: string;
		min?: string;
		max?: string;
		disabled?: boolean;
		readonly?: boolean;
		showTime?: boolean;
		placeholder?: string;
		size?: 'xs' | 'sm' | 'md';
		clearable?: boolean;
		onchange?: (value: string | null) => void;
		class?: string;
	}

	let {
		value = $bindable(''),
		label,
		id,
		name,
		min,
		max,
		disabled = false,
		readonly = false,
		showTime = false,
		placeholder = 'Pick a date',
		size = 'md',
		clearable = true,
		onchange,
		class: className
	}: Props = $props();

	// Cally registers custom elements and touches `document` at import time — client only.
	let callyReady = $state(false);
	onMount(() => {
		void import('cally').then(() => {
			callyReady = true;
		});
	});

	const uid = $props.id();

	const preference = $derived(normalizeDateFormat(page.data?.user?.date_format));
	const locale = $derived(resolveDateFormatLocale(preference));
	const firstDayOfWeek = $derived(getFirstDayOfWeek(preference));

	const uniqueId = $derived(id || `${uid}-date`);
	const popoverId = $derived(`${uniqueId}-popover`);
	const timePopoverId = $derived(`${uniqueId}-time-popover`);
	const anchorName = $derived(`--${uniqueId.replace(/[^a-zA-Z0-9_-]/g, '')}`);
	const timeAnchorName = $derived(`${anchorName}-time`);

	const datePart = $derived(value && value.includes('T') ? value.split('T')[0] : value || '');
	const hasTime = $derived(!!(value && value.includes('T')));
	const timePart = $derived(hasTime ? value?.split('T')[1]?.substring(0, 5) || '00:00' : '00:00');

	const dateHint = $derived(dateInputPlaceholder(preference));
	const displayTime = $derived(hasTime ? timePart : 'HH:mm');
	const hourOptions = Array.from({ length: 24 }, (_, index) => index);
	let dateDraft = $state('');
	let timeDraft = $state('');
	let dateFocused = $state(false);
	let timeFocused = $state(false);
	let dateError = $state('');
	let timeError = $state('');
	let dateInput: HTMLInputElement | undefined = $state();
	let timeInput: HTMLInputElement | undefined = $state();
	let rememberedTime = '00:00';
	const draftDate = $derived(parseDateInput(dateDraft, preference));

	$effect(() => {
		if (!dateFocused && !dateError && !timeError) dateDraft = formatDateInput(datePart, preference);
	});
	$effect(() => {
		if (!timeFocused && !dateError && !timeError) timeDraft = hasTime ? timePart : '';
		if (hasTime) rememberedTime = timePart;
	});

	function publish(next: string) {
		value = next;
		onchange?.(next);
	}

	function commitTypedDate(final = false) {
		if (disabled || readonly) return;
		const parsed = parseDateInput(dateDraft, preference);
		const rangeError = parsed && ((minDate && parsed < minDate) || (maxDate && parsed > maxDate));
		if (!parsed || rangeError) {
			if (!final) return;
			dateError = dateDraft.trim()
				? rangeError
					? 'Choose a date within the allowed range.'
					: `Enter a valid date (${dateHint}).`
				: '';
			dateInput?.setCustomValidity(dateError);
			publish('');
			return;
		}
		dateError = '';
		dateInput?.setCustomValidity('');
		if (final) dateDraft = formatDateInput(parsed, preference);
		if (!timeError)
			publish(showTime ? `${parsed}T${parseTimeInput(timeDraft) || rememberedTime}` : parsed);
	}

	function commitTypedTime(final = false) {
		if (disabled || readonly) return;
		const parsed = parseTimeInput(timeDraft);
		const date = draftDate || datePart;
		if (!parsed || !date) {
			if (!final) return;
			if (!timeDraft.trim() && date) {
				timeError = '';
				timeInput?.setCustomValidity('');
				publish(date);
				return;
			}
			timeError = 'Enter a time from 00:00 to 23:59.';
			timeInput?.setCustomValidity(timeError);
			publish('');
			return;
		}
		timeError = '';
		timeInput?.setCustomValidity('');
		rememberedTime = parsed;
		if (final) timeDraft = parsed;
		if (!dateError) publish(`${date}T${parsed}`);
	}

	function handleTypedKey(event: KeyboardEvent, commit: () => void) {
		if (event.key !== 'Enter') return;
		event.preventDefault();
		event.stopPropagation();
		commit();
	}

	const clock = $derived.by(() => {
		const match = /^(\d{1,2}):(\d{2})/.exec(timePart);
		const hours = Math.min(23, Math.max(0, Number(match?.[1] ?? 0) || 0));
		const minutes = Math.min(59, Math.max(0, Number(match?.[2] ?? 0) || 0));
		return {
			hours,
			minutes
		};
	});
	const minuteOptions = Array.from({ length: 60 }, (_, index) => index);

	const minDate = $derived(min ? min.split('T')[0] : undefined);
	const maxDate = $derived(max ? max.split('T')[0] : undefined);

	const sizeClass = $derived(size === 'xs' ? 'input-xs' : size === 'sm' ? 'input-sm' : '');

	const canClearDate = $derived(!!(clearable && datePart && !readonly && !disabled));
	const canClearTime = $derived(!!(clearable && hasTime && !readonly && !disabled));
	const controlHeightClass = $derived(size === 'md' ? 'date-input-md' : '');

	let popoverElement: HTMLDivElement | undefined = $state();

	function handleCalendarChange(e: Event) {
		const target = e.currentTarget as HTMLElement & { value: string };
		const newDate = target.value;
		if (!newDate) return;
		dateError = '';
		dateInput?.setCustomValidity('');
		dateDraft = formatDateInput(newDate, preference);

		if (showTime) {
			value = `${newDate}T${timePart || '00:00'}`;
		} else {
			value = newDate;
		}

		onchange?.(value);
		popoverElement?.hidePopover();
	}

	const listenForCalendarChange: Attachment<HTMLElement> = (element) => {
		element.addEventListener('change', handleCalendarChange);
		return () => element.removeEventListener('change', handleCalendarChange);
	};

	const capturePopover: Attachment<HTMLDivElement> = (element) => {
		popoverElement = element;
		const detachFlip = attachPopoverFlip(element, () => document.getElementById(uniqueId), 320);
		return () => {
			detachFlip();
			if (popoverElement === element) popoverElement = undefined;
		};
	};

	function commitTime(hours: number, minutes: number) {
		const date = draftDate || datePart;
		if (!date) return;
		timeError = '';
		timeInput?.setCustomValidity('');
		const next = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
		timeDraft = next;
		value = `${date}T${next}`;
		onchange?.(value);
	}

	function selectHour(hour: number) {
		commitTime(hour, clock.minutes);
	}

	function selectMinute(minute: number) {
		commitTime(clock.hours, minute);
	}

	const scrollTimeSelection: Attachment<HTMLElement> = (element) => {
		const detachFlip = attachPopoverFlip(
			element,
			() => document.getElementById(`${uniqueId}-time`),
			360
		);
		const onToggle = (event: Event) => {
			if ((event as ToggleEvent).newState !== 'open') return;
			element.querySelectorAll('[aria-pressed="true"]').forEach((node) => {
				node.scrollIntoView({ block: 'center' });
			});
		};
		element.addEventListener('toggle', onToggle);
		return () => {
			detachFlip();
			element.removeEventListener('toggle', onToggle);
		};
	};

	function handleClearDate() {
		dateError = timeError = '';
		dateDraft = timeDraft = '';
		dateInput?.setCustomValidity('');
		timeInput?.setCustomValidity('');
		rememberedTime = '00:00';
		value = '';
		onchange?.('');
	}

	function handleClearTime() {
		timeError = '';
		timeDraft = '';
		timeInput?.setCustomValidity('');
		if (!datePart) {
			handleClearDate();
			return;
		}
		value = datePart;
		onchange?.(datePart);
	}
</script>

{#if label}
	<label class="field-label" for={uniqueId}>{label}</label>
{/if}

<div class={['date-field flex w-full min-w-0 flex-col', showTime && 'is-timed', className]}>
	<div class="date-field-row">
		<div class={['date-input-date', canClearDate && 'join']}>
			<div
				class={[
					'input date-input-trigger font-normal',
					sizeClass,
					controlHeightClass,
					canClearDate && 'join-item'
				]}
				style:anchor-name={anchorName}
				class:input-error={Boolean(dateError)}
			>
				<input
					bind:this={dateInput}
					id={uniqueId}
					type="text"
					inputmode="text"
					autocomplete="off"
					class="typed-date"
					placeholder={dateHint}
					aria-label={label || 'Date'}
					aria-invalid={Boolean(dateError)}
					aria-describedby={dateError ? `${uniqueId}-error` : undefined}
					{disabled}
					{readonly}
					value={dateDraft}
					onfocus={() => (dateFocused = true)}
					oninput={(event) => {
						dateDraft = event.currentTarget.value;
						commitTypedDate();
					}}
					onblur={() => {
						commitTypedDate(true);
						dateFocused = false;
					}}
					onkeydown={(event) => handleTypedKey(event, () => commitTypedDate(true))}
				/>
				<button
					type="button"
					class="picker-button"
					popovertarget={popoverId}
					disabled={disabled || readonly}
					aria-label="Open calendar"
					title="Open calendar"><CalendarIcon class="size-4" /></button
				>
			</div>

			{#if canClearDate}
				<button
					type="button"
					class={['input date-input-clear join-item', sizeClass, controlHeightClass]}
					onclick={handleClearDate}
					aria-label="Clear date"
				>
					<CloseIcon class="h-4 w-4" />
				</button>
			{/if}
		</div>

		{#if showTime}
			<div class={['date-input-time-wrap', canClearTime && 'join']}>
				<div
					class={[
						'input date-input-time font-normal',
						sizeClass,
						controlHeightClass,
						canClearTime && 'join-item'
					]}
					style:anchor-name={timeAnchorName}
					class:input-error={Boolean(timeError)}
				>
					<input
						bind:this={timeInput}
						id={`${uniqueId}-time`}
						type="text"
						inputmode="text"
						autocomplete="off"
						class="typed-time"
						placeholder="HH:mm"
						maxlength="5"
						aria-label="Time (24-hour)"
						aria-invalid={Boolean(timeError)}
						aria-describedby={timeError ? `${uniqueId}-time-error` : undefined}
						disabled={disabled || (!datePart && !draftDate)}
						{readonly}
						value={timeDraft}
						onfocus={() => (timeFocused = true)}
						oninput={(event) => {
							timeDraft = event.currentTarget.value;
							commitTypedTime();
						}}
						onblur={() => {
							commitTypedTime(true);
							timeFocused = false;
						}}
						onkeydown={(event) => handleTypedKey(event, () => commitTypedTime(true))}
					/>
					<button
						type="button"
						class="picker-button"
						popovertarget={timePopoverId}
						disabled={disabled || readonly || (!datePart && !draftDate)}
						aria-label="Open time picker"
						title="Open time picker"><ClockIcon class="size-4" /></button
					>
				</div>

				{#if canClearTime}
					<button
						type="button"
						class={['input date-input-clear join-item', sizeClass, controlHeightClass]}
						onclick={handleClearTime}
						aria-label="Clear time"
					>
						<CloseIcon class="h-4 w-4" />
					</button>
				{/if}
			</div>
		{/if}
	</div>
</div>

<div
	{@attach capturePopover}
	popover
	id={popoverId}
	class="dropdown bg-base-100 rounded-box shadow-sm"
	style:position-anchor={anchorName}
>
	{#if callyReady}
		<calendar-date
			class="cally"
			{@attach listenForCalendarChange}
			value={datePart || undefined}
			min={minDate}
			max={maxDate}
			{locale}
			{firstDayOfWeek}
		>
			<svg
				aria-label="Previous"
				class="fill-current size-4"
				slot="previous"
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
			>
				<path d="M15.75 19.5 8.25 12l7.5-7.5"></path>
			</svg>
			<svg
				aria-label="Next"
				class="fill-current size-4"
				slot="next"
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
			>
				<path d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
			</svg>
			<calendar-month></calendar-month>
		</calendar-date>
	{/if}
</div>

{#if showTime}
	<div
		{@attach scrollTimeSelection}
		popover
		id={timePopoverId}
		class="dropdown time-popover bg-base-100 rounded-box shadow-sm"
		style:position-anchor={timeAnchorName}
	>
		<p class="mb-2 text-center text-base font-semibold tabular-nums">{displayTime}</p>
		<div class="time-picker">
			<div class="time-col">
				<span class="time-col-label">Hour</span>
				<div class="time-col-list">
					{#each hourOptions as hour (hour)}
						{@const selected = hour === clock.hours}
						<button
							type="button"
							class={['btn btn-sm', selected ? 'btn-primary' : 'btn-ghost']}
							aria-pressed={selected}
							onclick={() => selectHour(hour)}
						>
							{String(hour).padStart(2, '0')}
						</button>
					{/each}
				</div>
			</div>
			<div class="time-col">
				<span class="time-col-label">Minute</span>
				<div class="time-col-list">
					{#each minuteOptions as minute (minute)}
						{@const selected = minute === clock.minutes}
						<button
							type="button"
							class={['btn btn-sm', selected ? 'btn-primary' : 'btn-ghost']}
							aria-pressed={selected}
							onclick={() => selectMinute(minute)}
						>
							{String(minute).padStart(2, '0')}
						</button>
					{/each}
				</div>
			</div>
		</div>
	</div>
{/if}

{#if dateError}<p id={`${uniqueId}-error`} class="text-xs text-error mt-1" role="alert">
		{dateError}
	</p>{/if}
{#if timeError}<p id={`${uniqueId}-time-error`} class="text-xs text-error mt-1" role="alert">
		{timeError}
	</p>{/if}

{#if name}
	<input type="hidden" {name} value={value ?? ''} />
{/if}

<style>
	.typed-date,
	.typed-time {
		width: 100%;
		min-width: 0;
		flex: 1;
		background: transparent;
		border: 0;
		outline: 0;
		font: inherit;
		color: inherit;
	}
	.typed-time {
		font-variant-numeric: tabular-nums;
	}
	.picker-button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		flex: 0 0 1.75rem;
		height: 1.75rem;
		opacity: 0.65;
		cursor: pointer;
		border-radius: 0.25rem;
	}
	.picker-button:hover {
		opacity: 1;
		background: var(--color-base-200);
	}
	.picker-button:focus-visible {
		outline: 2px solid var(--color-primary);
	}

	.date-field {
		container-type: inline-size;
	}

	.date-field-row {
		display: flex;
		width: 100%;
		min-width: 0;
		align-items: stretch;
		gap: 0.5rem;
	}

	.date-input-date {
		display: flex;
		flex: 1 1 auto;
		min-width: 0;
	}

	.date-input-trigger {
		width: 100%;
		max-width: none;
		min-width: 0;
		flex: 1 1 auto;
	}

	.date-input-time-wrap {
		display: flex;
		flex: 0 0 auto;
		min-width: 0;
		align-items: stretch;
	}

	.date-input-time {
		flex: 1 1 auto;
		width: 9.75rem;
		min-width: 9.75rem;
		max-width: 9.75rem;
		padding-inline: 0.65rem;
	}

	.date-input-md {
		height: 3rem;
		min-height: 3rem;
		font-size: 1rem;
	}

	.date-input-clear {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 3rem;
		min-width: 3rem;
		max-width: 3rem;
		padding-inline: 0;
		flex: 0 0 3rem;
		cursor: pointer;
	}

	.date-input-clear.input-sm,
	.date-input-clear.input-xs {
		width: 2rem;
		min-width: 2rem;
		max-width: 2rem;
		flex-basis: 2rem;
	}

	.time-popover {
		padding: 0.75rem;
	}

	.time-picker {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.time-col {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.time-col:has(.time-col-list) {
		min-width: 4.25rem;
	}

	.time-col-label {
		font-size: 0.75rem;
		line-height: 1rem;
		font-weight: 600;
		opacity: 0.6;
	}

	.time-col-list {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		max-height: 14rem;
		overflow-y: auto;
		scrollbar-width: thin;
		padding-inline: 0.1rem;
	}

	.time-col-list .btn {
		width: 100%;
	}

	@container (max-width: 22rem) {
		.is-timed .date-field-row {
			flex-direction: column;
		}

		.is-timed .date-input-time-wrap,
		.is-timed .date-input-time {
			flex: 1 1 auto;
			width: 100%;
			min-width: 0;
			max-width: none;
		}
	}
</style>
