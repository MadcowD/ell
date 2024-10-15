import pytest
from ell.configurator import Config, Provider


class MockProvider(Provider):
    def provider_call_function(self, *args, **kwargs):
        pass

    def translate_from_provider(self, *args, **kwargs):
        pass

    def translate_to_provider(self, *args, **kwargs):
        pass


class MockOpenAIProvider(MockProvider):
    pass


class MockCustomProvider(MockOpenAIProvider):
    pass


class MockAnthropicProvider(MockProvider):
    pass


class TestProviderOverride:
    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def MockOpenAIClient(self):
        return type('MockOpenAIClient', (), {})

    @pytest.fixture
    def MockAnthropicClient(self):
        return type('MockAnthropicClient', (), {})

    def test_exact_match_provider(self, config, MockOpenAIClient):
        provider = MockOpenAIProvider()
        config.register_provider(provider, MockOpenAIClient)

        assert config.get_provider_for(MockOpenAIClient) == provider

    def test_subclass_match_provider(self, config, MockOpenAIClient):
        provider = MockProvider()
        config.register_provider(provider, MockOpenAIClient)

        CustomOpenAIClient = type('CustomOpenAIClient', (MockOpenAIClient,), {})

        assert config.get_provider_for(CustomOpenAIClient) == provider

    def test_most_specific_subclass_match(self, config, MockOpenAIClient):
        CustomOpenAIClient = type('CustomOpenAIClient', (MockOpenAIClient,), {})

        base_provider = MockProvider()
        openai_provider = MockOpenAIProvider()
        custom_provider = MockCustomProvider()
        config.register_provider(base_provider, object)
        config.register_provider(openai_provider, MockOpenAIClient)
        config.register_provider(custom_provider, CustomOpenAIClient)

        assert config.get_provider_for(CustomOpenAIClient) == custom_provider
        assert config.get_provider_for(MockOpenAIClient) == openai_provider

    def test_multiple_inheritance(self, config, MockOpenAIClient, MockAnthropicClient):
        openai_provider = MockOpenAIProvider()
        anthropic_provider = MockAnthropicProvider()
        config.register_provider(openai_provider, MockOpenAIClient)
        config.register_provider(anthropic_provider, MockAnthropicClient)

        HybridClient = type('HybridClient', (MockOpenAIClient, MockAnthropicClient), {})

        assert config.get_provider_for(HybridClient) == openai_provider

    def test_no_match_provider(self, config, MockOpenAIClient):
        provider = MockProvider()
        config.register_provider(provider, MockOpenAIClient)

        assert config.get_provider_for(str) is None

    def test_type_and_instance_input(self, config, MockOpenAIClient):
        provider = MockProvider()
        config.register_provider(provider, MockOpenAIClient)

        assert config.get_provider_for(MockOpenAIClient) == provider
        # For testing with an instance, we need to create one
        mock_instance = MockOpenAIClient()
        assert config.get_provider_for(type(mock_instance)) == provider

    def test_custom_provider_inheritance(self, config, MockOpenAIClient):
        CustomOpenAIClient = type('CustomOpenAIClient', (MockOpenAIClient,), {})
        VeryCustomOpenAIClient = type('VeryCustomOpenAIClient', (CustomOpenAIClient,), {})

        base_provider = MockProvider()
        openai_provider = MockOpenAIProvider()
        custom_provider = MockCustomProvider()

        config.register_provider(base_provider, object)
        config.register_provider(openai_provider, MockOpenAIClient)
        config.register_provider(custom_provider, CustomOpenAIClient)

        assert config.get_provider_for(MockOpenAIClient) == openai_provider
        assert config.get_provider_for(CustomOpenAIClient) == custom_provider
        assert config.get_provider_for(VeryCustomOpenAIClient) == custom_provider
