# Principles for developing ell

Some principles for developing ell that we pick up along the way.

1. went missing
2. went missing..
1. the user shouldn't wait to find out they're missing something:
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

2. no unreadable side-effects.
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


4. api providers are the single source of truth for model information
    - we will never implement Model("gpt-4", Capabilities(vision=True))
    - always rely on the api to tell you if you're using something a model can't do
    - in that sense ell.simple should be the thinnest possible wrapper around the api

5. ell is a library not a framework
    - we are building pytorch not keras. nice agent frameworks etc can exist on top of ell, but are not a part of ell itself. ell is meant to give you all of the building blocks to build systems.
    - in the meta programming space, we will support standardized building blocks (optimizers, established prompt compilers, etc) but not too frameworky. 
      (this is actually is a sticky point and drawing the line will always be hard, but initially this is good.)

6. less abstraction is better
   - more single files , less multi file abstractions
   - you should just be able to read the source & understand.

7. ell studio is not ell
    - ell studio is an exception in that we can bloat it as much as we need to make the dx beautiful.