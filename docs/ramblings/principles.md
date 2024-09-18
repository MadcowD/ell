# Principles for developing ell

1. <grab form discord>
2. <grab form discord>
3. the user shouldn't wait to find out they're missing something:
    Consider caching
    ```
    import ell

    @ell.simple
    def fn(): return "prompt"

    with ell.cache(fn):
        fn()
    ```
    If I don't have a store installed, this shit will break when i get to the ell.cache.

    We prefer to have store enable caching; that is the cache contextmanager is only enabled if we have a store:

    ```
    import ell
    
    store = ell.stores.SQLiteStore("mystore")
    ell.use_store(store)
    
    @ell.simple
    def fn(): return "prompt"

    with ell.store.cache(lmp):
        fn()
    ```

4. no unreadable side-effects.
   ```
   store = ell.stores.SQLiteStore("mystore")
   ell.use_store(store)
   ```
   is preferred to:
   ```
   store = ell.stores.SQLiteStore("mystore")
   store.install()
    ```
   This is a side-effect.
