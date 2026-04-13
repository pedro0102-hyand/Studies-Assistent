import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** Só utilizadores autenticados */
    requiresAuth?: boolean
    /** Redireciona para início se já autenticado (login/registo) */
    guestOnly?: boolean
  }
}
