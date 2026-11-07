<script lang="ts">
	import type { PageData } from './$types';
	import type { UserStats } from '#lib/types.js';
	import PageHeader from '#lib/components/ui/PageHeader.svelte';
	import LocationCard from '#lib/components/cards/LocationCard.svelte';
	import CalendarAgenda from '#lib/components/calendar/CalendarAgenda.svelte';
	import { apiEventsToDisplayEvents } from '#lib/calendar/events.js';
	import { dateFormatFromUser, formatDisplayDate } from '#lib/dateFormat.js';
	import { getDistance, getElevation } from '#lib/index.js';
	import { t } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import Plus from '~icons/mdi/plus';
	import ArrowRight from '~icons/mdi/arrow-right';

	let { data }: { data: PageData } = $props();
	let user = $derived(data.user);
	let stats: UserStats | null = $derived(data.props.stats);
	let recentLocations = $derived(data.props.recentLocations);
	let upcomingTrips = $derived(data.props.upcomingTrips);
	let activeTrip = $derived(data.props.activeTrip);
	let dateFormat = $derived(dateFormatFromUser(user));
	let measurementSystem = $derived(user?.measurement_system || 'metric');
	let agendaEvents = $derived(
		apiEventsToDisplayEvents(
			data.props.upcomingEvents,
			'event',
			Intl.DateTimeFormat().resolvedOptions().timeZone,
			{ eventTimezone: $t('calendar.event timezone'), localTimezone: $t('calendar.your timezone') },
			dateFormat
		)
			.filter((event) => event.start.split('T')[0] >= new Date().toISOString().split('T')[0])
			.slice(0, 5)
	);
	function formatTime(seconds: number) {
		return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
	}
</script>

<svelte:head
	><title>{$t('dashboard.page_title')} | AdventureLog</title><meta
		name="description"
		content="Your places, upcoming trips, and travel statistics."
	/></svelte:head
>

<div class="app-page">
	<PageHeader
		title={$t('dashboard.page_title')}
		description={$t('profile.your_journey_at_a_glance')}
		eyebrow={user?.first_name || user?.username || 'AdventureLog'}
	>
		<a href="/map" class="btn btn-outline btn-sm">{$t('navbar.map')}</a>
		<a href="/locations?new=1" class="btn btn-primary btn-sm"
			><Plus class="w-4 h-4" />{$t('map.add_location')}</a
		>
	</PageHeader>

	{#if data.props.loadError}<div class="alert alert-warning mb-6">
			{$t('dashboard.stats_error')}
		</div>{/if}

	{#if stats}
		<div class="metric-grid">
			<a href="/locations"
				><span class="metric-label">{$t('locations.locations')}</span><span class="metric-number"
					>{stats.location_count}</span
				><span class="metric-caption"
					>{stats.visited_location_count} {$t('adventures.visited').toLowerCase()}</span
				></a
			>
			<a href="/worldtravel"
				><span class="metric-label">{$t('profile.visited_countries')}</span><span
					class="metric-number"
					>{stats.visited_country_count}<span class="text-base text-base-content/40 font-normal">
						/ {stats.total_countries}</span
					></span
				><span class="metric-caption"
					>{stats.total_countries > 0
						? Math.round((stats.visited_country_count / stats.total_countries) * 100)
						: 0}% {$t('home.of_world').toLowerCase()}</span
				></a
			>
			<a href="/worldtravel"
				><span class="metric-label">{$t('profile.visited_cities')}</span><span class="metric-number"
					>{stats.visited_city_count}</span
				><span class="metric-caption"
					>{stats.visited_region_count} {$t('profile.visited_regions').toLowerCase()}</span
				></a
			>
			<a href="/collections"
				><span class="metric-label">{$t('navbar.collections')}</span><span class="metric-number"
					>{stats.trips_count}</span
				><span class="metric-caption"
					>{upcomingTrips.length} {$t('calendar.upcoming').toLowerCase()}</span
				></a
			>
		</div>
	{/if}

	<div class="dashboard-columns">
		<div class="min-w-0 space-y-10">
			<section>
				<div class="section-heading">
					<div>
						<h2>{$t('dashboard.recently_updated')}</h2>
						<p>{$t('home.latest_travel_experiences')}</p>
					</div>
					<a href="/locations" class="text-link">{$t('dashboard.view_all')}</a>
				</div>
				{#if recentLocations.length > 0}
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
						{#each recentLocations.slice(0, 6) as adventure (adventure.id)}<LocationCard
								{adventure}
								readOnly
								{user}
							/>{/each}
					</div>
				{:else}
					<div class="empty-state">
						<h3>{$t('dashboard.no_recent_locations')}</h3>
						<p>{$t('adventures.no_adventures_message')}</p>
						<a href="/locations?new=1" class="btn btn-primary btn-sm">{$t('map.add_location')}</a>
					</div>
				{/if}
			</section>
			{#if stats && stats.activities_overall.total_count > 0}
				<section class="surface p-6">
					<div class="section-heading">
						<h2>{$t('dashboard.activity_highlights')}</h2>
						<span class="text-sm text-base-content/60"
							>{stats.activities_overall.total_count} {$t('adventures.activities')}</span
						>
					</div>
					<dl class="grid grid-cols-2 sm:grid-cols-4 gap-6">
						<div>
							<dt class="metric-label">{$t('adventures.total_distance')}</dt>
							<dd class="mt-2 text-xl font-medium">
								{getDistance(measurementSystem, stats.activities_overall.total_distance)}
								<span class="text-sm text-base-content/50"
									>{measurementSystem === 'imperial' ? 'mi' : 'km'}</span
								>
							</dd>
						</div>
						<div>
							<dt class="metric-label">{$t('adventures.moving_time')}</dt>
							<dd class="mt-2 text-xl font-medium">
								{formatTime(stats.activities_overall.total_moving_time)}
							</dd>
						</div>
						<div>
							<dt class="metric-label">{$t('adventures.elevation_gain')}</dt>
							<dd class="mt-2 text-xl font-medium">
								{getElevation(measurementSystem, stats.activities_overall.total_elevation_gain)}
								<span class="text-sm text-base-content/50"
									>{measurementSystem === 'imperial' ? 'ft' : 'm'}</span
								>
							</dd>
						</div>
						<div>
							<dt class="metric-label">{$t('adventures.calories')}</dt>
							<dd class="mt-2 text-xl font-medium">
								{Math.round(stats.activities_overall.total_calories)}
							</dd>
						</div>
					</dl>
				</section>
			{/if}
		</div>
		<aside class="min-w-0 space-y-8">
			<section class="surface p-6">
				<div class="section-heading">
					<h2>{$t('dashboard.whats_next')}</h2>
					<a href="/collections" class="text-link">{$t('dashboard.view_all')}</a>
				</div>
				{#if activeTrip}<a
						href="/collections/{activeTrip.id}"
						class="block border-b border-base-300 pb-4 mb-4"
						><span class="badge badge-success mb-2">{$t('dashboard.active_trip')}</span>
						<h3 class="font-semibold text-lg">{activeTrip.name}</h3>
						<p class="text-sm text-base-content/60 mt-1">
							{activeTrip.location_count}
							{$t('locations.locations').toLowerCase()}
						</p></a
					>{/if}
				{#if upcomingTrips.length > 0}
					<div class="space-y-4">
						{#each upcomingTrips.slice(0, 3) as trip (trip.id)}<a
								href="/collections/{trip.id}"
								class="flex items-center justify-between gap-3"
								><div class="min-w-0">
									<h3 class="font-medium truncate">{trip.name}</h3>
									<p class="text-xs text-base-content/55 mt-1">
										{trip.start_date
											? formatDisplayDate(trip.start_date, dateFormat, { timeZone: 'UTC' })
											: $t('adventures.planned')} · {trip.location_count}
										{$t('locations.locations').toLowerCase()}
									</p>
								</div>
								<ArrowRight class="h-4 w-4 text-base-content/40 shrink-0" /></a
							>{/each}
					</div>
				{:else if !activeTrip}<p class="text-sm text-base-content/60">
						{$t('dashboard.no_upcoming_trips')}
					</p>
					<a href="/collections?new=1" class="btn btn-outline btn-sm mt-4"
						>{$t('dashboard.my_collections')}</a
					>{/if}
				{#if data.props.inviteCount > 0}<a
						class="text-link block mt-4"
						href="/collections?view=invites"
						>{$t('dashboard.pending_invites')}: {data.props.inviteCount}</a
					>{/if}
			</section>
			<section>
				<div class="section-heading">
					<h2>{$t('calendar.upcoming_agenda')}</h2>
					<a class="text-link" href="/calendar">{$t('navbar.calendar')}</a>
				</div>
				<CalendarAgenda
					events={agendaEvents}
					emptyMessage={$t('calendar.no_upcoming_events')}
					on:select={(event) => {
						const path = event.detail.extendedProps.url;
						if (path?.startsWith('/')) void goto(path);
					}}
				/>
			</section>
			<section>
				<h2 class="font-semibold mb-2">{$t('dashboard.quick_links')}</h2>
				<div class="journal-shortcuts">
					<a href="/map">{$t('navbar.map')}<ArrowRight class="w-4 h-4 opacity-40" /></a><a
						href="/worldtravel"
						>{$t('home.explore_world')}<ArrowRight class="w-4 h-4 opacity-40" /></a
					><a href="/settings?tab=integrations"
						>{$t('settings.integrations')}<ArrowRight class="w-4 h-4 opacity-40" /></a
					>
				</div>
			</section>
		</aside>
	</div>
</div>
