import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_auth/dex-trading')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_auth/dex-trading"!</div>
}
