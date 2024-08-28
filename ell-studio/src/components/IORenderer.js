import React from 'react';





const typeMatchers = {
  ToolResult: (data) => data && typeof data === 'object' && 'tool_call_id' in data && 'result' in data,
  ToolCall: (data) => data && typeof data === 'object' && 'tool' in data && 'params' in data,
  ContentBlock: (data) => data && typeof data === 'object' && ['text', 'image', 'audio', 'tool_call', 'parsed', 'tool_result'].some(key => key in data),
  Message: (data) => data && typeof data === 'object' && 'role' in data && 'content' in data,
};

const renderField = (key, value, customRenderers) => (
  <React.Fragment key={key}>
    <span className="text-sky-300">{key}</span>=<RecursiveObjectRenderer data={value} customRenderers={customRenderers} />
  </React.Fragment>
);

const renderFields = (data, customRenderers) => (
  Object.entries(data).map(([key, value], index, arr) => (
    <React.Fragment key={key}>
      {renderField(key, value, customRenderers)}
      {index < arr.length - 1 && ', '}
    </React.Fragment>
  ))
);

const typeRenderers = {
  ToolResult: (data, customRenderers) => (
    <span className="text-gray-300">
      <span className="text-blue-400">ToolResult</span>(
      {renderFields(data, customRenderers)}
      )
    </span>
  ),
  ToolCall: (data, customRenderers) => (
    <span className="text-gray-300">
      <span className="text-purple-400">ToolCall</span>(
      {renderFields(data, customRenderers)}
      )
    </span>
  ),
  ContentBlock: (data, customRenderers) => {
    const type = Object.keys(data).find(key => ['text', 'image', 'audio', 'tool_call', 'parsed', 'tool_result'].includes(key));
    return (
      <span className="text-gray-300">
        <span className="text-orange-400">ContentBlock</span>(
        {renderField(type, data[type], customRenderers)}
        )
      </span>
    );
  },
  Message: (data, customRenderers) => {
    const { role, content } = data;

    const renderContent = () => {
      if (content.length === 1) {
        const block = content[0];
        if (block.text) {
          return <span className="text-green-300">"{block.text}"</span>;
        } else if (block.image) {
          return <span className="text-green-300">"{block.image}"</span>;
        } else if (block.audio) {
          return <span className="text-green-300">"{block.audio}"</span>;
        } else if (block.tool_call || block.parsed || block.tool_result) {
          return <RecursiveObjectRenderer data={block[Object.keys(block)[0]]} customRenderers={customRenderers} />;
        }
      }
      
      return (
        <span className="text-gray-300">
          [
          {content.map((block, index) => (
            <React.Fragment key={index}>
              {index > 0 && ', '}
              <RecursiveObjectRenderer data={block} customRenderers={customRenderers} />
            </React.Fragment>
          ))}
          ]
        </span>
      );
    };

    return (
      <span className="text-gray-300">
        <span className="text-teal-400">Message</span>(
        {renderContent()},
        <span className="text-sky-300"> role</span>=<span className="text-green-300">"{role}"</span>
        )
      </span>
    );
  },
};

const RecursiveObjectRenderer = ({ data, customRenderers = [] }) => {
  // Add type matchers to the custom renderers
  const allRenderers = [
    ...Object.entries(typeMatchers).map(([type, match]) => ({
      match,
      render: (data) => typeRenderers[type](data, customRenderers)
    })),
    ...customRenderers
  ];

  // Check if any custom renderer matches the current data
  for (const { match, render } of allRenderers) {
    if (match(data)) {
      return render(data);
    }
  }

  if (Array.isArray(data)) {
    return (
      <span className="text-gray-300">
        [
        {data.map((item, index) => (
          <React.Fragment key={index}>
            <RecursiveObjectRenderer data={item} customRenderers={customRenderers} />
            {index < data.length - 1 && ', '}
          </React.Fragment>
        ))}
        ]
      </span>
    );
  }

  if (typeof data === 'object' && data !== null) {
    return (
      <span className="text-gray-300">
        {'{'}
        {Object.entries(data).map(([key, value], index, arr) => (
          <React.Fragment key={key}>
            <span className="text-sky-300">{key}</span>: <RecursiveObjectRenderer data={value} customRenderers={customRenderers} />
            {index < arr.length - 1 && ', '}
          </React.Fragment>
        ))}
        {'}'}
      </span>
    );
  }

  if (typeof data === 'string') {
    return <span className="text-green-300">"{data}"</span>;
  }

  if (typeof data === 'number') {
    return <span className="text-yellow-300">{data}</span>;
  }

  if (typeof data === 'boolean') {
    return <span className="text-purple-300">{String(data)}</span>;
  }

  if (data === null) {
    return <span className="text-red-300">null</span>;
  }

  return <span className="text-gray-300">{JSON.stringify(data)}</span>;
};

const Indent = ({ level, children }) => (
  <div style={{ marginLeft: `${level * 20}px` }}>{children}</div>
);

const renderNonInline = (data, customRenderers, level = 0) => {
  if (Array.isArray(data)) {
    return (
      <div>
        [
        {data.map((item, index) => (
          <Indent key={index} level={level + 1}>
            {renderNonInline(item, customRenderers, level + 1)}
            {index < data.length - 1 && ','}
          </Indent>
        ))}
        <Indent level={level}>]</Indent>
      </div>
    );
  }

  if (typeof data === 'object' && data !== null) {
    if (typeMatchers.Message(data)) {
      return renderNonInlineMessage(data, customRenderers, level);
    }
    if (typeMatchers.ContentBlock(data)) {
      return renderNonInlineContentBlock(data, customRenderers, level);
    }
    if (typeMatchers.ToolCall(data)) {
      return renderNonInlineToolCall(data, customRenderers, level);
    }
    if (typeMatchers.ToolResult(data)) {
      return renderNonInlineToolResult(data, customRenderers, level);
    }

    return (
      <div>
        {'{'}
        {Object.entries(data).map(([key, value], index, arr) => (
          <Indent key={key} level={level + 1}>
            <span className="text-sky-300">{key}</span>: {renderNonInline(value, customRenderers, level + 1)}
            {index < arr.length - 1 && ','}
          </Indent>
        ))}
        <Indent level={level}>{'}'}</Indent>
      </div>
    );
  }

  return <span className="text-green-300">{JSON.stringify(data)}</span>;
};

const renderNonInlineMessage = (data, customRenderers, level) => {
  const { role, content } = data;

  const renderContent = () => {
    if (content.length === 1) {
      const block = content[0];
      if (block.text || block.image || block.audio) {
        return <span className="text-green-300">"{block[Object.keys(block)[0]]}"</span>;
      }
    }
    return renderNonInline(content, customRenderers, level + 1);
  };

  return (
    <div>
      <span className="text-teal-400">Message</span>(
      <Indent level={level + 1}>
        {renderContent()},
      </Indent>
      <Indent level={level + 1}>
        <span className="text-sky-300">role</span>: <span className="text-green-300">"{role}"</span>
      </Indent>
      <Indent level={level}>)</Indent>
    </div>
  );
};

const renderNonInlineContentBlock = (data, customRenderers, level) => {
  const type = Object.keys(data).find(key => ['text', 'image', 'audio', 'tool_call', 'parsed', 'tool_result'].includes(key));
  return (
    <div>
      <span className="text-orange-400">ContentBlock</span>(
      <Indent level={level + 1}>
        <span className="text-sky-300">{type}</span>: {renderNonInline(data[type], customRenderers, level + 1)}
      </Indent>
      <Indent level={level}>)</Indent>
    </div>
  );
};

const renderNonInlineToolCall = (data, customRenderers, level) => {
  return (
    <div>
      <span className="text-purple-400">ToolCall</span>(
      {Object.entries(data).map(([key, value], index, arr) => (
        <Indent key={key} level={level + 1}>
          <span className="text-sky-300">{key}</span>: {renderNonInline(value, customRenderers, level + 1)}
          {index < arr.length - 1 && ','}
        </Indent>
      ))}
      <Indent level={level}>)</Indent>
    </div>
  );
};

const renderNonInlineToolResult = (data, customRenderers, level) => {
  return (
    <div>
      <span className="text-blue-400">ToolResult</span>(
      {Object.entries(data).map(([key, value], index, arr) => (
        <Indent key={key} level={level + 1}>
          <span className="text-sky-300">{key}</span>: {renderNonInline(value, customRenderers, level + 1)}
          {index < arr.length - 1 && ','}
        </Indent>
      ))}
      <Indent level={level}>)</Indent>
    </div>
  );
};

const IORenderer = ({ content, customRenderers = [], inline = true }) => {
  try {
    const parsedContent = JSON.parse(content);
    return (
      <div className="text-sm font-mono">
        {inline ? (
          <RecursiveObjectRenderer data={parsedContent} customRenderers={customRenderers} />
        ) : (
          renderNonInline(parsedContent, customRenderers)
        )}
      </div>
    );
  } catch {
    return <span className="text-sm text-gray-300">{content}</span>;
  }
};

export default IORenderer;