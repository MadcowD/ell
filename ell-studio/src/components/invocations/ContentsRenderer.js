
import { useBlob } from '../../hooks/useBackend';
import IORenderer from '../IORenderer';

export function ContentsRenderer({ item, field, ...rest }) {
    const contents = item.contents;
    console.log(contents[field]);

    if (contents.is_external && !contents.is_external_loaded) {
      return <div>Loading...</div>;
    } else {
      return <IORenderer content={contents[field]} {...rest} />;
    }
}