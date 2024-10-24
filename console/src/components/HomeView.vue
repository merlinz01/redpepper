<template>
  <div class="d-flex flex-column align-center ga-5 ma-5">
    <h1 class="text-primary">Welcome to RedPepper</h1>
    <v-btn to="/login" color="primary" variant="elevated">Log in</v-btn>
    <v-row class="ma-5 ga-5">
      <v-card to="/agents" title="Agents" />
      <v-card to="/events" title="Events" />
      <v-card to="/commands" title="Commands" />
      <v-card to="/data" title="Data Editor" />
      <v-card to="/help" title="Help" />
    </v-row>
  </div>
</template>
