<script lang="ts">
	import { page } from '$app/state';
</script>

<svelte:head><title>{page.status} | AdventureLog</title></svelte:head>
<div class="app-page">
	<div class="surface max-w-lg mx-auto my-12 p-8">
		<span class="page-eyebrow">{page.status}</span>
		<h1 class="text-2xl font-semibold">
			{page.status === 404 ? 'Page not found' : 'Unable to load this page'}
		</h1>
		<p class="mt-3 text-base-content/60">
			{page.status === 404
				? 'The link may have changed, or this page may no longer be available.'
				: 'Please try again in a moment. Your saved travel records are unchanged.'}
		</p>
		<a class="btn btn-primary btn-sm mt-6" href="/">Return home</a>
	</div>
</div>
