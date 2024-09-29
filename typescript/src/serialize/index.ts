import { WriteInvocationInput, WriteLMPInput } from "./types"
import { config } from "../configurator"
import * as logging from "../util/_logging"

const logger = logging.getLogger('serialize')

export const serializeLMP = async (args: Omit<WriteLMPInput, 'commit_message' | 'version_number'>) => {
  try {
    const serializer = config.getStore()
    if (!serializer) {
      return
    }
    // todo. see if we can defer some of these responsibilities to the serializer/backend
    // for now we'll get things working the same as python
    // todo. we need to come up with a fully qualified name
    const otherVersions = await serializer.getVersionsByFqn(args.name)
    if (otherVersions.length === 0) {
      // We are the first version of the LMP!
      return await serializer.writeLMP({
        ...args,
        commit_message: 'Initial version',
        version_number: 1,
      })
    }

    const newVersionNumber = otherVersions[0].version_number + 1
    return await serializer.writeLMP({
      ...args,
      // FIXME. check if auto commit and create a commit message if so
      commit_message: 'New version',
      version_number: newVersionNumber,
    })
  } catch (e) {
    logger.error(`Error serializing LMP: ${e}`)
  }
}

export const serializeInvocation = async (input: WriteInvocationInput) => {
  try {
    const serializer = config.getStore()
    if (!serializer) {
      return
    }
    return await serializer.writeInvocation(input)
  } catch (e) {
    logger.error(`Error serializing invocation: ${e}`)
  }
}