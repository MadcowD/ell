
lmp() <- result_lstrs[]  ...compute... another_lmp(result_lstrs[]) <- new_result[]

invocation -> lstrs <- another_invoke
                |
                |
         third invocation    (trace(3rd invocation) = [invocation, another_invocation]
                              

orignators in ell2a will always be invocation ids.

when i get a new lstr from calling an LMP, i will get the id of the invocaiton that produced it as the sole originator


some_lmp() -> y:= lstr("content", originator=invocation_id of that call.)

y += x 

some_lmp() -> y:= lstr("content", originator=(invocation_id), instantenous_meta_data={
      logits, 
      completion id
      model id
      invocation_id,
      lmp_id.
})



y.invocation_id


y += " 123"
y = some_lmp(meta_data = True)

# Should the user ever know about invocations or traces or originators?