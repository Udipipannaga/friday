import { defineConfig } from '@playwright/test';
export default defineConfig({testDir:'e2e', timeout:30000, workers:1, use:{baseURL:process.env.FRIDAY_E2E_URL || 'http://localhost:8011', channel:'msedge', headless:true}, reporter:'list'});
