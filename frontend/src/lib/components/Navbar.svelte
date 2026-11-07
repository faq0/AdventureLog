<script lang="ts">
	import { run } from 'svelte/legacy';

	import { goto } from '$app/navigation';
	import { openCommandPalette } from '#lib/search/palette.js';

	import DotsHorizontal from '~icons/mdi/dots-horizontal';
	import Calendar from '~icons/mdi/calendar';
	import AboutModal from './AboutModal.svelte';
	import AccountMultiple from '~icons/mdi/account-multiple';
	import MapMarker from '~icons/mdi/map-marker';
	import FormatListBulletedSquare from '~icons/mdi/format-list-bulleted-square';
	import Earth from '~icons/mdi/earth';
	import Magnify from '~icons/mdi/magnify';
	import Map from '~icons/mdi/map';
	import Menu from '~icons/mdi/menu';
	import Avatar from './Avatar.svelte';
	import { page } from '$app/state';
	import { t, locale, locales } from 'svelte-i18n';
	import { themes } from '#lib';
	import { enhance, type SubmitFunction } from '$app/forms';
	import { onMount } from 'svelte';
	import { shouldFlipDropdownUp } from '#lib/utils/flipDropdown.js';

	interface Props {
		data: any;
	}

	let { data }: Props = $props();
	let theme = $state('');
	let query: string = $state('');
	let isAboutModalOpen: boolean = $state(false);
	let isMac = $state(false);
	let settingsOpen = $state(false);
	let mobileOpen = $state(false);
	let settingsOpenUpward = $state(false);
	let settingsMenuEl: HTMLDivElement | undefined = $state();

	run(() => {
		if (page.url.pathname === '/search') {
			query = page.url.searchParams.get('q') || page.url.searchParams.get('query') || '';
		}
	});

	let modifierHint = $derived(isMac ? '⌘K' : 'Ctrl+K');

	function openSearch(initialQuery = '') {
		openCommandPalette(initialQuery || query);
	}

	// Event listener for opening search palette
	function handleKeydown(event: KeyboardEvent) {
		if (
			event.key === '/' &&
			!['INPUT', 'TEXTAREA'].includes((event.target as HTMLElement)?.tagName) &&
			showFullNav
		) {
			event.preventDefault();
			openSearch();
		}
	}

	onMount(() => {
		isMac = /Mac|iPhone|iPad/.test(navigator.platform);
		document.addEventListener('keydown', handleKeydown);
		// @ts-ignore
		theme =
			document.documentElement.getAttribute('data-theme') ||
			(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

		return () => {
			document.removeEventListener('keydown', handleKeydown);
		};
	});

	let languages: { [key: string]: string } = {
		en: 'English',
		de: 'Deutsch',
		es: 'Español',
		fr: 'Français',
		it: 'Italiano',
		nl: 'Nederlands',
		sv: 'Svenska',
		zh: '中文',
		pl: 'Polski',
		ko: '한국어',
		no: 'Norsk',
		ru: 'Русский',
		ja: '日本語',
		ar: 'العربية',
		pt: 'Português',
		'pt-br': 'Português (Brasil)',
		ro: 'Română',
		sk: 'Slovenský',
		tr: 'Türkçe',
		uk: 'Українська',
		hu: 'Magyar',
		ca: 'Català',
		cs: 'Čeština',
		ta: 'தமிழ்',
		sq: 'Shqip',
		id: 'Bahasa Indonesia',
		gsw: 'Alemannisch',
		lb: 'Lëtzebuergesch'
	};

	const submitLocaleChange = (event: Event) => {
		const select = event.target as HTMLSelectElement;
		const newLocale = select.value;
		document.cookie = `locale=${newLocale}; path=/; max-age=${60 * 60 * 24 * 365}; SameSite=Lax`;
		locale.set(newLocale);
		window.location.reload();
	};

	const submitThemeChange = (event: Event) => {
		// @ts-ignore
		const theme = event.target.value;
		// @ts-ignore
		const themeForm = event.target.parentNode;
		themeForm.action = `/?/setTheme&theme=${theme}`;
		themeForm.submit();
	};

	const submitUpdateTheme: SubmitFunction = ({ action }) => {
		const nextTheme = action.searchParams.get('theme');
		if (nextTheme) {
			document.documentElement.setAttribute('data-theme', nextTheme);
		}
	};

	function toggleSettingsMenu(event: MouseEvent) {
		event.stopPropagation();
		if (!settingsOpen) {
			settingsOpenUpward = shouldFlipDropdownUp(settingsMenuEl);
		}
		settingsOpen = !settingsOpen;
	}

	function closeSettingsMenu(event: MouseEvent) {
		if (!settingsOpen) return;
		if (settingsMenuEl?.contains(event.target as Node)) return;
		settingsOpen = false;
	}

	function handleSettingsKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') settingsOpen = false;
	}

	function openAbout() {
		settingsOpen = false;
		isAboutModalOpen = true;
	}
	// Navigation items for better organization
	const navigationItems = [
		{ path: '/locations', icon: MapMarker, label: 'locations.locations' },
		{ path: '/collections', icon: FormatListBulletedSquare, label: 'navbar.collections' },
		{ path: '/worldtravel', icon: Earth, label: 'navbar.worldtravel' },
		{ path: '/map', icon: Map, label: 'navbar.map' },
		{ path: '/calendar', icon: Calendar, label: 'navbar.calendar' },
		{ path: '/users', icon: AccountMultiple, label: 'navbar.users' }
	];

	const msPerDay = 1000 * 60 * 60 * 24;
	let subscription = $derived(data?.subscription);
	let cloudMode = $derived(data?.cloudMode);
	let hasAccess = $derived(data?.hasAccess ?? true);
	let trialEndsAt = $derived(
		subscription?.trial_ends_at ? new Date(subscription.trial_ends_at) : null
	);
	let daysRemaining = $derived(
		trialEndsAt ? Math.max(0, Math.ceil((trialEndsAt.getTime() - Date.now()) / msPerDay)) : null
	);
	let isTrial = $derived(subscription?.status === 'trial');
	let hasScheduledSubscription = $derived(Boolean(subscription?.stripe_subscription_id));
	let showTrialCta = $derived(isTrial && !hasScheduledSubscription);
	let showExpiredCta = $derived(!hasAccess);
	let showFullNav = $derived(data?.user && (!cloudMode || hasAccess));
	let pendingInviteCount = $derived(data?.pendingInviteCount ?? 0);
</script>

<svelte:window onclick={closeSettingsMenu} onkeydown={handleSettingsKeydown} />
{#if isAboutModalOpen}<AboutModal on:close={() => (isAboutModalOpen = false)} />{/if}

<header class="app-navigation">
	<div class="navigation-inner">
		<a class="wordmark" href={data.user ? '/dashboard' : '/'} aria-label="AdventureLog home">
			<span class="wordmark-symbol" aria-hidden="true">A</span>
			<span>AdventureLog</span>
		</a>
		{#if showFullNav}
			<nav class="desktop-navigation" aria-label="Main navigation">
				{#each navigationItems as item}
					<a
						href={item.path}
						class:current={page.url.pathname.startsWith(item.path)}
						aria-current={page.url.pathname.startsWith(item.path) ? 'page' : undefined}
					>
						{$t(item.label)}
						{#if item.path === '/collections' && pendingInviteCount > 0}<span class="nav-count"
								>{pendingInviteCount}</span
							>{/if}
					</a>
				{/each}
			</nav>
		{/if}
		<div class="navigation-actions">
			{#if showFullNav}
				<button
					type="button"
					class="search-trigger"
					onclick={() => openSearch()}
					aria-label={$t('search.open_palette')}
				>
					<Magnify class="h-4 w-4" />
					<span class="search-label">{$t('navbar.search')}</span>
					<kbd>{modifierHint}</kbd>
				</button>
			{/if}
			{#if data.user && cloudMode && subscription}
				{#if showExpiredCta}<a href="/subscribe" class="btn btn-warning btn-sm"
						>{$t('navbar.access_paused')}</a
					>
				{:else if showTrialCta}<a href="/subscribe" class="btn btn-primary btn-sm"
						>{$t('navbar.trial_days_left', { values: { days: daysRemaining ?? 0 } })}</a
					>{/if}
			{/if}
			{#if data.user}<Avatar user={data.user} cloudMode={data.cloudMode} />
			{:else}<a class="btn btn-primary btn-sm" href="/login">{$t('auth.login')}</a>{/if}
			<div
				bind:this={settingsMenuEl}
				class="dropdown dropdown-end"
				class:dropdown-open={settingsOpen}
				class:dropdown-close={!settingsOpen}
			>
				<button
					type="button"
					class="btn btn-ghost btn-square btn-sm"
					aria-label="Appearance and language"
					aria-haspopup="menu"
					aria-expanded={settingsOpen}
					onclick={toggleSettingsMenu}><DotsHorizontal class="w-5 h-5" /></button
				>
				{#if settingsOpen}
					<div class="dropdown-content appearance-menu surface" role="menu">
						<a
							class="menu-link"
							href="https://adventurelog.app/docs/"
							target="_blank"
							rel="noreferrer">{$t('navbar.documentation')}</a
						>
						<a
							class="menu-link"
							href="https://github.com/faq0/AdventureLog"
							target="_blank"
							rel="noreferrer">Source code</a
						>
						<button class="menu-link" type="button" onclick={openAbout}>{$t('navbar.about')}</button
						>
						<div class="menu-separator"></div>
						<form method="POST" use:enhance>
							<label class="field-label" for="app-language">{$t('navbar.language_selection')}</label
							>
							<select
								id="app-language"
								class="select select-sm w-full"
								onchange={submitLocaleChange}
								bind:value={$locale}
							>
								{#each $locales as loc (loc)}<option value={loc}>{languages[loc]}</option>{/each}
							</select>
							<input type="hidden" name="locale" value={$locale} />
						</form>
						<form method="POST" use:enhance={submitUpdateTheme}>
							<label class="field-label" for="app-theme">{$t('navbar.theme_selection')}</label>
							<select
								id="app-theme"
								class="select select-sm w-full"
								bind:value={theme}
								onchange={submitThemeChange}
							>
								{#each themes as option}<option value={option.name}
										>{$t(`navbar.themes.${option.name}`)}</option
									>{/each}
							</select>
						</form>
					</div>
				{/if}
			</div>
			{#if showFullNav}
				<button
					class="btn btn-ghost btn-square btn-sm mobile-navigation-toggle"
					type="button"
					aria-label="Navigation"
					aria-controls="mobile-navigation"
					aria-expanded={mobileOpen}
					onclick={() => (mobileOpen = !mobileOpen)}><Menu class="w-5 h-5" /></button
				>
			{/if}
		</div>
	</div>
	{#if mobileOpen && showFullNav}
		<nav id="mobile-navigation" class="mobile-navigation" aria-label="Mobile navigation">
			<a href="/dashboard" onclick={() => (mobileOpen = false)}>{$t('dashboard.page_title')}</a>
			{#each navigationItems as item}<a
					href={item.path}
					class:current={page.url.pathname.startsWith(item.path)}
					aria-current={page.url.pathname.startsWith(item.path) ? 'page' : undefined}
					onclick={() => (mobileOpen = false)}>{$t(item.label)}</a
				>{/each}
			<a href="/settings" onclick={() => (mobileOpen = false)}>{$t('navbar.settings')}</a>
		</nav>
	{/if}
</header>

<style>
	.app-navigation {
		position: sticky;
		top: 0;
		z-index: 999;
		background: var(--color-base-100);
		border-bottom: 1px solid var(--color-base-300);
	}
	.navigation-inner {
		display: flex;
		align-items: center;
		gap: 2rem;
		height: 64px;
		max-width: 1600px;
		margin-inline: auto;
		padding-inline: 2rem;
	}
	.wordmark {
		display: inline-flex;
		align-items: center;
		gap: 0.65rem;
		flex-shrink: 0;
		font-size: 1.1rem;
		font-weight: 650;
		letter-spacing: -0.04em;
	}
	.wordmark-symbol {
		display: grid;
		place-items: center;
		width: 27px;
		height: 29px;
		background: var(--color-primary);
		color: var(--color-primary-content);
		font-size: 18px;
		font-weight: 500;
		border-radius: 7px;
		letter-spacing: -0.07em;
	}
	.desktop-navigation {
		display: flex;
		align-items: center;
		gap: 0.15rem;
		flex: 1;
	}
	.desktop-navigation a {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.5rem 0.65rem;
		border-radius: 0.4rem;
		font-size: 0.825rem;
		font-weight: 500;
		white-space: nowrap;
		color: color-mix(in srgb, var(--color-base-content) 65%, transparent);
	}
	.desktop-navigation a:hover,
	.desktop-navigation .current {
		background: var(--color-base-200);
		color: var(--color-base-content);
	}
	.nav-count {
		font-size: 0.65rem;
		font-variant-numeric: tabular-nums;
		background: var(--color-primary);
		color: var(--color-primary-content);
		padding: 0 0.3rem;
		border-radius: 0.25rem;
	}
	.navigation-actions {
		display: flex;
		align-items: center;
		gap: 0.65rem;
		margin-left: auto;
	}
	.search-trigger {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		min-height: 34px;
		padding: 0.4rem 0.6rem;
		color: color-mix(in srgb, var(--color-base-content) 55%, transparent);
		border: 1px solid var(--color-base-300);
		border-radius: 0.5rem;
		cursor: pointer;
		font-size: 0.8rem;
	}
	.search-trigger:hover {
		color: var(--color-base-content);
		background: var(--color-base-200);
	}
	kbd {
		font-size: 0.65rem;
		margin-left: 1.5rem;
		opacity: 0.75;
	}
	.appearance-menu {
		width: 260px;
		padding: 0.75rem;
		margin-top: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	.appearance-menu form {
		padding: 0.4rem 0.35rem;
	}
	.menu-link {
		display: block;
		padding: 0.5rem 0.4rem;
		font-size: 0.85rem;
		border-radius: 0.3rem;
		text-align: left;
	}
	.menu-link:hover {
		background: var(--color-base-200);
	}
	.menu-separator {
		border-top: 1px solid var(--color-base-300);
		margin-block: 0.4rem;
	}
	.mobile-navigation-toggle {
		display: none;
	}
	.mobile-navigation {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.3rem;
		padding: 0.75rem 1rem;
		border-top: 1px solid var(--color-base-300);
	}
	.mobile-navigation a {
		padding: 0.7rem;
		font-size: 0.9rem;
		border-radius: 0.4rem;
	}
	.mobile-navigation .current {
		background: var(--color-base-200);
		color: var(--color-primary);
	}
	@media (max-width: 1250px) {
		.navigation-inner {
			gap: 1rem;
			padding-inline: 1.25rem;
		}
		.search-label,
		kbd {
			display: none;
		}
		.search-trigger {
			border: 0;
		}
		.desktop-navigation a {
			padding-inline: 0.5rem;
		}
	}
	@media (max-width: 1023px) {
		.desktop-navigation {
			display: none;
		}
		.mobile-navigation-toggle {
			display: inline-flex;
		}
	}
	@media (max-width: 480px) {
		.navigation-inner {
			padding-inline: 1rem;
			gap: 0.5rem;
		}
		.navigation-actions {
			gap: 0.2rem;
		}
		.wordmark {
			font-size: 1rem;
		}
		.wordmark-symbol {
			display: none;
		}
	}
</style>
