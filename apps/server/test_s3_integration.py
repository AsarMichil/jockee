#!/usr/bin/env python3
"""
Test script for S3 integration
"""
import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.s3_storage import S3StorageService
from app.services.audio_fetcher import AudioFetcher
from app.core.config import settings

async def test_s3_integration():
    """Test S3 storage service integration."""
    print("Testing S3 Integration...")
    print(f"S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"CloudFront Domain: {settings.CLOUDFRONT_DOMAIN}")
    
    try:
        # Test S3 storage service
        s3_storage = S3StorageService()
        print("✅ S3StorageService initialized successfully")
        
        # Test key generation
        test_key = s3_storage.generate_s3_key("Test Artist", "Test Song")
        print(f"✅ Generated S3 key: {test_key}")
        
        # Test CloudFront URL generation
        cloudfront_url = s3_storage.generate_cloudfront_url(test_key)
        print(f"✅ Generated CloudFront URL: {cloudfront_url}")
        
        # Test audio fetcher initialization
        audio_fetcher = AudioFetcher()
        print("✅ AudioFetcher with S3 support initialized successfully")
        
        print("\n🎉 All S3 integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ S3 integration test failed: {e}")
        return False

async def test_file_upload(delete_before_upload=False, keep_s3_file=False):
    """Test uploading a small test file to S3."""
    print("\nTesting file upload to S3...")
    print(f"Options: delete_before_upload={delete_before_upload}, keep_s3_file={keep_s3_file}")
    
    try:
        # Create a small test file
        test_file_path = "/tmp/test_audio.txt"
        with open(test_file_path, "w") as f:
            f.write("This is a test audio file content")
        
        s3_storage = S3StorageService()
        test_key = s3_storage.generate_s3_key("Test Artist", "Test Upload")
        
        # Delete existing file if requested
        if delete_before_upload:
            print("🗑️ Checking for and deleting any existing test file...")
            existing_file = await s3_storage.file_exists(test_key)
            if existing_file:
                deleted = await s3_storage.delete_file(test_key)
                if deleted:
                    print("✅ Existing test file deleted successfully")
                else:
                    print("⚠️ Failed to delete existing test file")
            else:
                print("ℹ️ No existing test file found")
        
        # Upload the test file
        result = await s3_storage.upload_file(test_file_path, test_key)
        
        if result["success"]:
            print(f"✅ File uploaded successfully to S3: {test_key}")
            
            # Test file existence
            exists = await s3_storage.file_exists(test_key)
            if exists:
                print("✅ File existence check passed")
                
                # Get file info
                file_info = await s3_storage.get_file_info(test_key)
                if file_info:
                    print(f"✅ File info retrieved: {file_info['file_size']} bytes")
                    
                    # Generate CloudFront URL
                    url = s3_storage.generate_cloudfront_url(test_key)
                    print(f"✅ CloudFront URL: {url}")
                    
                    # Clean up - delete test file (unless keep_s3_file is True)
                    if not keep_s3_file:
                        deleted = await s3_storage.delete_file(test_key)
                        if deleted:
                            print("✅ Test file cleaned up successfully")
                        else:
                            print("⚠️ Failed to clean up test file")
                    else:
                        print(f"🔒 Keeping S3 test file: {test_key}")
                else:
                    print("❌ Failed to get file info")
            else:
                print("❌ File existence check failed")
        else:
            print(f"❌ File upload failed: {result['error']}")
            return False
        
        # Clean up local test file
        os.unlink(test_file_path)
        
        print("🎉 File upload test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        return False

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test S3 integration for the Auto-DJ application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_s3_integration.py                    # Run normal tests
  python test_s3_integration.py --keep-s3-file     # Keep test file in S3
  python test_s3_integration.py --delete-before    # Delete existing file before upload
  python test_s3_integration.py --delete-before --keep-s3-file  # Both options
        """
    )
    
    parser.add_argument(
        "--delete-before",
        action="store_true",
        help="Delete any existing test file from S3 before uploading"
    )
    
    parser.add_argument(
        "--keep-s3-file",
        action="store_true", 
        help="Keep the test file in S3 after upload (don't delete it)"
    )
    
    parser.add_argument(
        "--skip-upload-test",
        action="store_true",
        help="Skip the file upload test and only run basic integration test"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    import asyncio
    
    # Parse command-line arguments
    args = parse_arguments()
    
    print("🔧 S3 Integration Test Suite")
    print("=" * 40)
    
    if args.delete_before:
        print("🗑️ Will delete existing files before upload")
    if args.keep_s3_file:
        print("🔒 Will keep S3 test files after upload")
    if args.skip_upload_test:
        print("⏭️ Skipping file upload test")
    print()
    
    # Run basic integration test
    success1 = asyncio.run(test_s3_integration())
    
    if success1:
        if not args.skip_upload_test:
            # Run file upload test if basic test passed
            success2 = asyncio.run(test_file_upload(
                delete_before_upload=args.delete_before,
                keep_s3_file=args.keep_s3_file
            ))
            
            if success1 and success2:
                print("\n🎉 All tests passed! S3 integration is ready.")
                if args.keep_s3_file:
                    print("📁 Note: Test files were kept in S3 as requested.")
                sys.exit(0)
            else:
                print("\n❌ Some tests failed. Check your configuration.")
                sys.exit(1)
        else:
            print("\n🎉 Basic integration test passed! (File upload test skipped)")
            sys.exit(0)
    else:
        print("\n❌ Basic integration test failed. Check your AWS credentials and configuration.")
        sys.exit(1) 