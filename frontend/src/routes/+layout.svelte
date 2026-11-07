<script lang="ts">
	import { browser } from '$app/env';
	import { untrack } from 'svelte';
	import { register, init, locale, waitLocale } from 'svelte-i18n';
	import { UmamiAnalyticsEnv } from '@lukulent/svelte-umami';

	// Register your translations for each locale
	register('en', () => import('../locales/en.json'));
	register('es', () => import('../locales/es.json'));
	register('fr', () => import('../locales/fr.json'));
	register('de', () => import('../locales/de.json'));
	register('it', () => import('../locales/it.json'));
	register('zh', () => import('../locales/zh.json'));
	register('nl', () => import('../locales/nl.json'));
	register('sv', () => import('../locales/sv.json'));
	register('pl', () => import('../locales/pl.json'));
	register('ko', () => import('../locales/ko.json'));
	register('no', () => import('../locales/no.json'));
	register('ru', () => import('../locales/ru.json'));
	register('ja', () => import('../locales/ja.json'));
	register('ar', () => import('../locales/ar.json'));
	register('pt-br', () => import('../locales/pt-br.json'));
	register('ro', () => import('../locales/ro.json'));
	register('sk', () => import('../locales/sk.json'));
	register('tr', () => import('../locales/tr.json'));
	register('uk', () => import('../locales/uk.json'));
	register('hu', () => import('../locales/hu.json'));
	register('ca', () => import('../locales/ca.json'));
	register('cs', () => import('../locales/cs.json'));
	register('pt', () => import('../locales/pt.json'));
	register('sq', () => import('../locales/sq.json'));
	register('ta', () => import('../locales/ta.json'));
	register('id', () => import('../locales/id.json'));
	register('gsw', () => import('../locales/gsw.json'));
	register('lb', () => import('../locales/lb.json'));

	let { data, children } = $props();

	let locales = [
		'en',
		'es',
		'fr',
		'de',
		'it',
		'zh',
		'nl',
		'sv',
		'pl',
		'ko',
		'no',
		'ru',
		'ja',
		'ar',
		'pt',
		'pt-br',
		'ro',
		'sk',
		'tr',
		'uk',
		'hu',
		'ca',
		'cs',
		'ta',
		'sq',
		'id',
		'gsw',
		'lb'
	];

	if (browser) {
		const initialLocale = untrack(() => data.locale);
		init({
			fallbackLocale: locales.includes(navigator.language.split('-')[0])
				? navigator.language.split('-')[0]
				: 'en',
			initialLocale
		});
		// get the locale cookie if it exists and set it as the initial locale if it exists
		const localeCookie = document.cookie
			.split(';')
			.find((cookie) => cookie.trim().startsWith('locale='));
		if (localeCookie) {
			const localeValue = localeCookie.split('=')[1];
			locale.set(localeValue);
		}
	}

	import Navbar from '#lib/components/Navbar.svelte';
	import Toast from '#lib/components/Toast.svelte';
	import CommandPalette from '#lib/components/search/CommandPalette.svelte';
	import '../app.css';

	// Create a promise that resolves when the locale is ready
	export const localeLoaded = browser ? waitLocale() : Promise.resolve();
</script>

{#await localeLoaded}
	<!-- You can add a loading indicator here if needed -->
{:then}
	<a href="#main-content" class="skip-link">Skip to content</a>
	<Navbar {data} />
	{#if data.user}
		<CommandPalette />
	{/if}
	<Toast />
	<div id="main-content" tabindex="-1">{@render children?.()}</div>
{/await}

<UmamiAnalyticsEnv />

<svelte:head>
	<title>AdventureLog</title>
	<meta name="description" content="Your places, trips, and travel journal." />
</svelte:head>

<style>
	:global(html) {
		overflow-x: clip;
	}
	:global(body) {
		min-width: 320px;
	}
	.skip-link {
		position: fixed;
		top: 0.75rem;
		left: 1rem;
		z-index: 2000;
		transform: translateY(-200%);
		background: var(--color-base-100);
		color: var(--color-base-content);
		border: 1px solid var(--color-base-300);
		border-radius: 0.5rem;
		padding: 0.5rem 1rem;
	}
	.skip-link:focus {
		transform: translateY(0);
	}
</style>
