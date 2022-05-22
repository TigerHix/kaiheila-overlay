<script setup lang="ts">
import { computed } from "vue";
import { Options, User } from "./../models/Models";

const props = defineProps<{ options: Options; user: User; bottom: boolean }>();

function replaceWithDefaultPortrait(e: any) {
  e.target.src = '/portraits/default.png';
}

const name = computed(() => props.options.custom_names[props.user.id] ?? props.user.nickname)
</script>

<template>
  <div>
    <div style="height: 480px; overflow: visible">
      <div
        class="flex relative items-center justify-center"
        style="max-width: 500%; width: 100%; height: 100%; overflow: visible"
      >
        <img
          @error="replaceWithDefaultPortrait"
          :src="'/portraits/' + user.id + '.png'"
          style="
            max-width: 500%;
            height: 100%;
            object-fit: cover;
            overflow: visible;
          "
          class="portrait"
          v-bind:class="{ speaking: user.talking }"
          :alt="name"
        />
        <template v-if="options.nametag">
          <div v-if="bottom" class="absolute nametag text-center" v-bind:class="{ speaking: user.talking }" :style="{ bottom: options.nametag_margin_bottom + 'px' }">
            {{ name }}
          </div>
          <div v-else class="absolute nametag" v-bind:class="{ speaking: user.talking }" :style="{ top: '-' + options.nametag_margin_top + 'px' }">
            {{ name }}
          </div>
        </template>
      </div>
    </div>
    <!-- {{ user.id }}
    {{ user.nickname }} -->
  </div>
</template>