<script lang="ts">
	import { t } from 'svelte-i18n';
	let { data } = $props();
	let background = $derived(data.props?.background);
</script>

<svelte:head
	><title>AdventureLog — Your travel journal</title><meta
		name="description"
		content="Keep places, plan trips, and revisit the details of your travels."
	/></svelte:head
>
<div class="app-page">
	<section class="welcome-layout">
		<div class="welcome-copy">
			<span class="page-eyebrow">AdventureLog</span>
			<h1>Your places.<br />Your travel journal.</h1>
			<p>Keep the places you’ve been, plan your next trip, and bring the details together.</p>
			<a href="/login" class="btn btn-primary">{$t('auth.login')}</a>
		</div>
		{#if background?.url}<figure class="welcome-photo">
				<img src={background.url} alt={background.location || 'Travel photography'} />
				<figcaption>{background.location || 'AdventureLog'}</figcaption>
			</figure>{/if}
	</section>
	<div class="welcome-features">
		<div>
			<span class="page-eyebrow">01</span>
			<h2>Keep your places</h2>
			<p>Photos, notes, dates, and the details you want to remember.</p>
		</div>
		<div>
			<span class="page-eyebrow">02</span>
			<h2>Plan a trip</h2>
			<p>Put locations, stays, and transport into an itinerary.</p>
		</div>
		<div>
			<span class="page-eyebrow">03</span>
			<h2>See your world</h2>
			<p>Explore your travel history on a map, country by country.</p>
		</div>
	</div>
</div>

<style>
	.welcome-layout {
		display: grid;
		grid-template-columns: 1fr 1fr;
		align-items: center;
		gap: 5rem;
		padding-block: 3rem;
	}
	.welcome-copy h1 {
		font-size: clamp(2.75rem, 5vw, 4.5rem);
		line-height: 1.1;
		letter-spacing: -0.055em;
		font-weight: 550;
		margin-top: 1rem;
	}
	.welcome-copy p {
		font-size: 1.1rem;
		line-height: 1.7;
		max-width: 25rem;
		margin-block: 1.5rem 2rem;
		color: color-mix(in srgb, var(--color-base-content) 60%, transparent);
	}
	.welcome-photo {
		position: relative;
		height: 470px;
		border-radius: 0.75rem;
		overflow: hidden;
		background: var(--color-base-300);
	}
	.welcome-photo img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	figcaption {
		position: absolute;
		bottom: 1rem;
		left: 1rem;
		color: #fff;
		background: #17251d99;
		padding: 0.25rem 0.6rem;
		font-size: 0.75rem;
		border-radius: 0.25rem;
	}
	.welcome-features {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 3rem;
		border-top: 1px solid var(--color-base-300);
		padding-block: 2.5rem;
	}
	.welcome-features h2 {
		font-size: 1.1rem;
		font-weight: 600;
	}
	.welcome-features p {
		font-size: 0.875rem;
		line-height: 1.7;
		margin-top: 0.6rem;
		color: color-mix(in srgb, var(--color-base-content) 60%, transparent);
	}
	@media (max-width: 767px) {
		.welcome-layout {
			grid-template-columns: 1fr;
			gap: 2rem;
			padding-top: 1rem;
		}
		.welcome-photo {
			height: 300px;
		}
		.welcome-features {
			grid-template-columns: 1fr;
			gap: 1.75rem;
		}
	}
</style>
