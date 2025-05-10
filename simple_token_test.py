#!/usr/bin/env python3
"""
Simple test of token authentication.
"""
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[SIMPLE_TOKEN_TEST] %(levelname)s - %(message)s')
logger = logging.getLogger("simple_token_test")

def main():
    """Run a simple token test"""
    logger.info("Starting simple token test")
    
    # Test the token manager
    try:
        from token_manager import TokenManager
        token_manager = TokenManager()
        logger.info(f"TokenManager initialized (expiry: {token_manager.token_expiry_days} days)")
        
        # Generate a token
        token = token_manager.generate_token(1, "test_user")
        logger.info(f"Token generated: {token}")
        
        # Validate the token
        payload = token_manager.validate_token(token)
        logger.info(f"Token validation result: {payload}")
        
        logger.info("✅ Basic token test PASSED!")
    except Exception as e:
        logger.error(f"❌ Error testing TokenManager: {e}")
        return 1
    
    # Test the enhanced token manager if available
    try:
        from enhanced_token_manager import EnhancedTokenManager
        enhanced_token_manager = EnhancedTokenManager()
        logger.info(f"EnhancedTokenManager initialized (expiry: {enhanced_token_manager.token_expiry_days} days)")
        
        # Generate a token
        enhanced_token = enhanced_token_manager.generate_token(2, "enhanced_user")
        logger.info(f"Enhanced token generated: {enhanced_token}")
        
        # Validate the token
        enhanced_payload = enhanced_token_manager.validate_token(enhanced_token)
        logger.info(f"Enhanced token validation result: {enhanced_payload}")
        
        logger.info("✅ Enhanced token test PASSED!")
    except Exception as e:
        logger.error(f"❌ Error testing EnhancedTokenManager: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
