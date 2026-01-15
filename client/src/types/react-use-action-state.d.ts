/**
 * React 19 useActionState type augmentation
 * 
 * The useActionState hook was added in React 19 but types may not be complete
 * in @types/react@19.0.0. This provides polyfill typing.
 */
import "react";

declare module "react" {
  /**
   * React 19 useActionState hook for handling async actions with pending states.
   * @see https://react.dev/reference/react/useActionState
   */
  function useActionState<State, Payload>(
    action: (state: Awaited<State>, payload: Payload) => State | Promise<State>,
    initialState: Awaited<State>,
    permalink?: string
  ): [state: Awaited<State>, dispatch: (payload: Payload) => void, isPending: boolean];
}
