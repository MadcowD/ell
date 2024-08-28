export const lstrCleanStringify = (obj_containing_lstrs, indentLevel = 2) => {
  return JSON.stringify(obj_containing_lstrs, (key, value) => {
    if (value && value.__lstr === true) {
      return value.content;
    }
    return value;
  }, indentLevel)
};
