<script setup lang="ts">
import { computed, ref } from 'vue'
import { Options, Payload, User } from './../models/Models'
import Portrait from './Portrait.vue';

const ws = new WebSocket('ws://localhost:8899')
const data = ref<Payload>()
const options: Options = {
  row_max: 7,
  hidden_ids: [],
  nametag: true,
  nametag_margin_top: 40,
  nametag_margin_bottom: 40,
  custom_names: {},
  current_users: undefined
}

ws.onmessage = e => {
  console.log(e.data)
  const parsed = JSON.parse(e.data)
  console.log(parsed)

  // let users = []
  // for (let i = 0; i < parsed.current_users.length; i++) {
  //   for (let j = 0; j < 13; j++) {
  //     users.push(parsed.current_users[i])
  //   }
  // }
  // parsed.current_users = users

  if (options.current_users) {
    parsed.current_users = JSON.parse(JSON.stringify(options.current_users));
    for (let user of parsed.current_users) {
      if (parsed.talking_users.includes(user.id)) {
        user.talking = true;
      }
    }
  }
  data.value = parsed
}

const uri = window.location.search.substring(1)
const params = new URLSearchParams(uri)
options.max_width = params.get('max_width') ? Number(params.get('max_width')) : options.max_width
options.hidden_ids = params.get('hidden_ids') ? params.get('hidden_ids')!.split(',') : options.hidden_ids
options.row_max = params.get('row_max') ? Number(params.get('row_max')) : options.row_max
options.nametag = params.get('nametag') ? params.get('nametag')!.toLowerCase() === 'true' : options.nametag
options.nametag_margin_top = params.get('nametag_margin_top') ? Number(params.get('nametag_margin_top')) : options.nametag_margin_top
options.nametag_margin_bottom = params.get('nametag_margin_bottom') ? Number(params.get('nametag_margin_bottom')) : options.nametag_margin_bottom
options.custom_names = params.get('custom_names') ? Object.fromEntries(params.get('custom_names')!.split(',').map(it => [it.split(':')[0], it.split(':')[1]])) : options.custom_names
options.current_users = params.get('current_users') ? JSON.parse(params.get('current_users')!) : options.current_users

console.log('Parsed options:')
console.log(options)

const visibleUsers = computed(() => data.value?.current_users.filter(it => !options.hidden_ids.includes(it.id)))

</script>

<template>
<div class="flex justify-center">
  <div class="flex justify-center" :style="{'max-width': options.max_width + 'px'}">
    <div class="w-10/12" v-if="visibleUsers">
      <div v-if="visibleUsers.length > options.row_max">
        <div class="grid" style="padding-left: 0px;" :style="{'grid-template-columns': `repeat(${Math.floor(visibleUsers.length / 2)}, minmax(0, 1fr))`}">
          <Portrait :options="options" :user="user" :bottom="false" v-for="user in visibleUsers.slice(0, visibleUsers.length / 2)" v-bind:key="user.id" />
        </div>
        <div class="grid" style="padding-left: 0px; margin-top: -310px;" :style="{'grid-template-columns': `repeat(${visibleUsers.length - Math.floor(visibleUsers.length / 2)}, minmax(0, 1fr))`}">
          <Portrait :options="options" :user="user" :bottom="true" v-for="user in visibleUsers.slice(visibleUsers.length / 2, visibleUsers.length)" v-bind:key="user.id" />
        </div>
      </div>
      <div v-else>
        <div class="grid grid-flow-col auto-cols-auto" style="padding-left: 0px;">
          <Portrait :options="options" :user="user" :bottom="true" v-for="user in visibleUsers" v-bind:key="user.id" />
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<style scoped>
</style>
