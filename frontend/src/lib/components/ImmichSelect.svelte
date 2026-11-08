<script lang="ts">
	import { run } from 'svelte/legacy';

	import { createEventDispatcher, onMount, untrack } from 'svelte';
	import { t } from 'svelte-i18n';
	import CheckIcon from '~icons/mdi/check';
	import CloseIcon from '~icons/mdi/close';
	import type { ImmichAlbum } from '#lib/types.js';
	import { debounce } from '#lib';
	import DateInput from './shared/DateInput.svelte';

	interface Props {
		// Props
		copyImmichLocally?: boolean;
		objectId?: string;
		contentType?: string;
		defaultDate?: string;
		adding?: boolean;
	}

	let {
		copyImmichLocally = false,
		objectId = '',
		contentType = 'location',
		defaultDate = '',
		adding = $bindable(false)
	}: Props = $props();

	// Component state
	const nearbyContentTypes = ['location', 'lodging', 'transportation', 'visit'];
	const supportsNearby = $derived(nearbyContentTypes.includes(contentType));
	let endpoint = $state('origin');
	let immichImages: any[] = $state([]);
	let immichSearchValue: string = $state('');
	let searchCategory: 'nearby' | 'search' | 'date' | 'album' = $state(
		untrack(() => (nearbyContentTypes.includes(contentType) ? 'nearby' : 'date'))
	);
	let radius = $state('500');
	let selectedIds = $state<Set<string>>(new Set());
	let addedIds = $state<Set<string>>(new Set());
	let requestVersion = 0;
	let immichError: string = $state('');
	let immichNextURL: string = $state('');
	let loading = $state(false);
	let albums: ImmichAlbum[] = $state([]);
	let currentAlbum: string = $state('');
	let selectedDate: string = $state(new Date().toISOString().split('T')[0]);

	$effect.pre(() => {
		if (defaultDate) {
			selectedDate = defaultDate;
		}
	});

	const dispatch = createEventDispatcher<{
		localImage: { file: File; immichId: string };
		remoteImmichSaved: Record<string, unknown>;
	}>();

	// Helper functions
	function clearAlbumSelection() {
		if (currentAlbum) {
			currentAlbum = '';
		}
	}

	function buildQueryParams(): string {
		const params = new URLSearchParams();

		if (immichSearchValue && searchCategory === 'search') {
			params.append('query', immichSearchValue);
		} else if (selectedDate && searchCategory === 'date') {
			params.append('date', selectedDate);
		}

		return params.toString();
	}

	// API functions
	async function fetchAssets(url: string, usingNext = false): Promise<void> {
		const version = ++requestVersion;
		loading = true;
		immichError = '';

		try {
			const res = await fetch(url);
			if (version !== requestVersion) return;

			if (!res.ok) {
				const data = await res.json();
				console.error('Error in fetchAssets:', data.message);
				immichError = data.message || $t(data.code || 'immich.fetch_error');
				return;
			}

			const data = await res.json();

			if (data.results && data.results.length > 0) {
				if (usingNext) {
					immichImages = [...immichImages, ...data.results];
				} else {
					immichImages = data.results;
				}
				immichNextURL = data.next || '';
			} else {
				if (!usingNext) immichImages = [];
				immichError =
					searchCategory === 'nearby'
						? 'No photos found within this distance. Try a wider radius, a date, or an album.'
						: $t('immich.no_items_found');
				immichNextURL = data.next || '';
			}
		} catch (error) {
			console.error('Error fetching assets:', error);
			immichError = $t('immich.fetch_error');
		} finally {
			loading = false;
		}
	}

	async function fetchAlbumAssets(albumId: string): Promise<void> {
		return fetchAssets(`/api/integrations/immich/albums/${albumId}`);
	}

	async function loadMoreImmich(): Promise<void> {
		if (!immichNextURL) return;

		// Convert absolute URL to relative path for frontend API proxy
		const url = new URL(immichNextURL, window.location.origin);
		const relativePath = url.pathname + url.search;

		return fetchAssets(relativePath, true);
	}

	async function saveSelectedPhotos() {
		adding = true;
		immichError = '';
		for (const imageId of selectedIds) {
			try {
				const res = await fetch('/api/images', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						immich_id: imageId,
						object_id: objectId,
						content_type: contentType,
						copy_locally: copyImmichLocally
					})
				});
				if (!res.ok)
					throw new Error(
						'Could not add a selected photo. Your selection has been kept so you can retry.'
					);
				dispatch('remoteImmichSaved', await res.json());
				addedIds = new Set([...addedIds, imageId]);
				selectedIds = new Set([...selectedIds].filter((id) => id !== imageId));
			} catch (error) {
				immichError = error instanceof Error ? error.message : 'Could not add photo.';
				break;
			}
		}
		adding = false;
	}

	// Event handlers
	const searchImmich = debounce(() => {
		_searchImmich();
	}, 500);

	async function _searchImmich(): Promise<void> {
		immichImages = [];
		return fetchAssets(`/api/integrations/immich/search/?${buildQueryParams()}`);
	}

	function handleSearchCategoryChange(category: 'nearby' | 'search' | 'date' | 'album') {
		requestVersion++;
		immichImages = [];
		immichNextURL = '';
		selectedIds = new Set();
		searchCategory = category;
		immichError = '';

		if (category !== 'album') {
			clearAlbumSelection();
		}
	}

	function handleImageSelect(image: { id: string }) {
		const next = new Set(selectedIds);
		if (next.has(image.id)) next.delete(image.id);
		else next.add(image.id);
		selectedIds = next;
	}

	// Lifecycle
	onMount(async () => {
		try {
			const res = await fetch('/api/integrations/immich/albums');

			if (res.ok) {
				const data = await res.json();
				albums = data;
			} else {
				console.warn('Failed to fetch Immich albums');
			}
		} catch (error) {
			console.error('Error fetching albums:', error);
		}
	});
	// Reactive statements
	run(() => {
		if (searchCategory === 'nearby' && objectId) {
			immichImages = [];
			void fetchAssets(
				`/api/integrations/immich/nearby/?object_id=${objectId}&content_type=${contentType}&endpoint=${endpoint}&radius=${radius}`
			);
		} else if (searchCategory === 'album' && currentAlbum) {
			immichImages = [];
			fetchAlbumAssets(currentAlbum);
		} else if (searchCategory === 'date' && selectedDate) {
			clearAlbumSelection();
			searchImmich();
		} else if (searchCategory === 'search') {
			clearAlbumSelection();
		}
	});
</script>

<!-- Search Category Tabs -->
<div class="flex flex-wrap gap-2 mb-3">
	{#if supportsNearby}
		<button
			type="button"
			class="btn btn-sm"
			class:btn-primary={searchCategory === 'nearby'}
			class:btn-ghost={searchCategory !== 'nearby'}
			disabled={adding}
			onclick={() => handleSearchCategoryChange('nearby')}>Near this place</button
		>
	{/if}
	<button
		class="btn btn-sm"
		class:btn-primary={searchCategory === 'search'}
		class:btn-ghost={searchCategory !== 'search'}
		onclick={() => handleSearchCategoryChange('search')}
	>
		{$t('navbar.search')}
	</button>
	<button
		class="btn btn-sm"
		class:btn-primary={searchCategory === 'date'}
		class:btn-ghost={searchCategory !== 'date'}
		onclick={() => handleSearchCategoryChange('date')}
	>
		{$t('immich.by_date')}
	</button>
	<button
		class="btn btn-sm"
		class:btn-primary={searchCategory === 'album'}
		class:btn-ghost={searchCategory !== 'album'}
		onclick={() => handleSearchCategoryChange('album')}
	>
		{$t('immich.by_album')}
	</button>
</div>

<!-- Search Controls -->
{#if searchCategory === 'nearby'}
	<div class="flex flex-wrap items-center gap-3">
		{#if contentType === 'transportation'}
			<label class="text-sm" for="nearby-endpoint">Near</label>
			<select
				id="nearby-endpoint"
				class="select select-sm w-auto"
				bind:value={endpoint}
				disabled={loading || adding}
			>
				<option value="origin">Departure</option><option value="destination">Arrival</option>
			</select>
		{/if}
		<label for="nearby-radius" class="text-sm">Distance from this place</label>
		<select
			id="nearby-radius"
			class="select select-sm w-auto"
			bind:value={radius}
			disabled={loading || adding}
		>
			<option value="100">100 m</option><option value="250">250 m</option><option value="500"
				>500 m</option
			><option value="1000">1 km</option><option value="5000">5 km</option>
		</select>
	</div>
	<p class="text-xs text-base-content/60 mt-2">
		Suggestions use photo GPS. Select the photos you want to add.
		{#if contentType === 'location'}The earliest capture time fills in your visit.{/if}
	</p>
{:else if searchCategory === 'search'}
	<div class="flex gap-2">
		<input
			type="text"
			placeholder={$t('immich.image_search_placeholder') + '...'}
			bind:value={immichSearchValue}
			class="input flex-1"
			disabled={loading || adding}
		/>
		<button
			type="submit"
			class="btn btn-primary btn-sm"
			class:loading
			disabled={loading || !immichSearchValue.trim()}
			onclick={searchImmich}
		>
			{$t('navbar.search')}
		</button>
	</div>
{:else if searchCategory === 'date'}
	<div class="flex gap-2 items-center">
		<DateInput
			id="date-picker"
			bind:value={selectedDate}
			disabled={loading || adding}
			clearable={false}
		/>
	</div>
{:else if searchCategory === 'album'}
	<select
		id="album-select"
		class="select w-full"
		bind:value={currentAlbum}
		disabled={loading || adding}
	>
		<option value="" disabled>
			{albums.length > 0 ? $t('immich.select_album') : $t('immich.loading_albums')}
		</option>
		{#each albums as album (album.id)}
			<option value={album.id}>{album.albumName}</option>
		{/each}
	</select>
{/if}

<!-- Error Message -->
{#if immichError}
	<div class="rounded-lg border border-base-300 bg-base-100 mt-3 p-3">
		<span class="text-sm">{immichError}</span>
	</div>
{/if}

<!-- Images Results (Inline) -->
{#if loading}<p class="text-sm text-base-content/60 py-4" role="status">Finding photos…</p>{/if}
{#if selectedIds.size > 0}
	<div
		class="sticky top-0 z-10 flex items-center justify-between gap-3 bg-base-100 border border-base-300 rounded-lg p-3 mt-3"
	>
		<span class="text-sm">{selectedIds.size} selected</span>
		<button
			type="button"
			class="btn btn-primary btn-sm"
			disabled={adding}
			onclick={saveSelectedPhotos}
			>{adding ? 'Adding photos…' : `Add selected (${selectedIds.size})`}</button
		>
	</div>
{/if}
{#if immichImages.length > 0}
	<div class="mt-4">
		<div class="flex items-center justify-between mb-3">
			<span class="text-sm text-base-content/70">
				{immichImages.length}
				{immichImages.length === 1 ? 'image' : 'images'} found
			</span>
			<button
				class="btn btn-ghost btn-xs"
				onclick={() => {
					immichImages = [];
					immichSearchValue = '';
					immichNextURL = '';
				}}
			>
				<CloseIcon class="h-4 w-4" />
			</button>
		</div>
		<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-96 overflow-y-auto">
			{#each immichImages as image (image.id)}
				<button
					type="button"
					class="card bg-base-100 border border-base-300 hover:border-primary transition-colors cursor-pointer group relative overflow-hidden"
					class:ring-2={selectedIds.has(image.id)}
					class:ring-primary={selectedIds.has(image.id)}
					aria-pressed={selectedIds.has(image.id)}
					aria-label={`Select photo${image.distance_meters != null ? `, ${image.distance_meters} m away` : ''}`}
					onclick={() => handleImageSelect(image)}
					disabled={loading || adding || addedIds.has(image.id)}
				>
					<figure class="aspect-square bg-base-200 overflow-hidden">
						<img
							src={image.image_url}
							alt="Immich"
							class="w-full h-full object-cover transition-transform group-hover:scale-105"
							loading="lazy"
						/>
					</figure>
					<div
						class="absolute top-2 right-2 w-6 h-6 rounded-full border-2 border-white shadow-sm flex items-center justify-center"
						class:bg-primary={selectedIds.has(image.id) || addedIds.has(image.id)}
						class:bg-neutral={!selectedIds.has(image.id)}
					>
						{#if selectedIds.has(image.id) || addedIds.has(image.id)}<CheckIcon
								class="w-4 h-4 text-white"
							/>{/if}
					</div>
					<div class="w-full px-2 py-2 text-left text-xs flex justify-between gap-2">
						<span>{image.localDateTime?.slice(0, 10) || 'Photo'}</span>
						<span
							>{addedIds.has(image.id)
								? 'Added'
								: image.distance_meters != null
									? `${image.distance_meters} m`
									: ''}</span
						>
					</div>
				</button>
			{/each}
		</div>

		<!-- Load More Button -->
		{#if immichNextURL}
			<div class="flex justify-center mt-3">
				<button
					class="btn btn-outline btn-sm btn-wide"
					onclick={loadMoreImmich}
					disabled={loading || adding}
				>
					{loading ? $t('immich.loading') : $t('immich.load_more')}
				</button>
			</div>
		{/if}
	</div>
{/if}
