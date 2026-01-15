// @ts-nocheck
import { defineConfig } from 'orval';

export default defineConfig({
  api: {
    input: {
      target: 'http://127.0.0.1:8000/openapi.json',
    },
    output: {
      mode: 'tags-split',
      target: 'src/api/endpoints',
      schemas: 'src/api/model',
      client: 'react-query',
      prettier: true,
      override: {
        mutator: {
          path: './src/server/dal.ts', // Use our custom DAL/Ky instance
          name: 'customInstance',
        },
        query: {
          useQuery: true,
          useInfinite: true,
        },
      },
    },
  },
});
